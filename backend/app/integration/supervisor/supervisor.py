"""
Supervisor — core orchestration engine.

Execution model:

  INPUT → PLAN → GOVERNANCE CHECK → EXECUTE → AGGREGATE → RESPONSE

Each stage is deterministic:
  - PLAN:      static intent → provider mapping (planner.py)
  - GOVERNANCE: pre-execution constraint enforcement (governance.py)
  - EXECUTE:   registry-resolved provider calls (executor.py)
  - AGGREGATE: merge results into unified response (aggregator.py)

There is no LLM in this pipeline. No randomness. No dynamic re-planning.
For a given (intent, claim_id), the output structure is always the same.

The supervisor is the only entry point for orchestrated tool calls.
No other module calls providers directly. The registry is the sole
source of provider instances.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from backend.app.integration.contracts.common import ProviderMode, ToolResultStatus
from backend.app.integration.mocks.errors import MockIntegrationError
from backend.app.integration.providers import ProviderName
from backend.app.integration.registry import IntegrationConfigError, ProviderRegistry

from .aggregator import aggregate
from .executor import execute_plan, _make_context, _dispatch_call, _call_with_retry
from .governance import enforce_governance
from .models import (
    ClaimIntent,
    GovernanceFlags,
    ProviderTrace,
    SupervisorRequest,
    SupervisorResponse,
    SupervisorStatus,
)
from .planner import build_plan, classify_intent

logger = logging.getLogger(__name__)


def run_supervisor(
    request: SupervisorRequest,
    registry: ProviderRegistry,
) -> SupervisorResponse:
    """
    Execute a claim intelligence request through the full supervisor pipeline.

    Args:
        request:  SupervisorRequest with claim_id, intent, and optional context.
        registry: The application registry (sole source of providers).

    Returns:
        SupervisorResponse with traces, aggregated result, and governance flags.

    Raises:
        IntegrationConfigError if governance constraints are violated. The
        caller (API endpoint) catches this and returns a 422 response.
    """
    request_id = str(uuid.uuid4())
    wall_start = time.perf_counter()

    logger.info(
        "Supervisor: START request_id=%s claim_id=%s intent=%s",
        request_id, request.claim_id, request.intent,
    )

    # --- PLAN ---
    intent = classify_intent(request.intent)
    providers_plan = build_plan(intent)
    logger.debug("Supervisor: plan=%s providers=%s", intent.value, providers_plan)

    # --- GOVERNANCE CHECK (before any provider call) ---
    try:
        enforce_governance(providers_plan, registry)
    except IntegrationConfigError as exc:
        logger.error("Supervisor: governance FAIL — %s", exc)
        raise

    # --- EXECUTE ---
    # Collect raw results alongside traces so the aggregator can inspect them.
    # The executor returns traces; we re-run a lightweight pass to collect
    # raw results for the aggregator. To keep the modules clean we do a single
    # combined execution here.
    ctx = _make_context(request.claim_id)
    traces: list[ProviderTrace] = []
    raw_results: dict[str, Any] = {}

    exec_start = time.perf_counter()
    for provider_name in providers_plan:
        t_start = time.perf_counter()
        method_dispatch = {
            ProviderName.CLAIMCENTER:  "get_claim",
            ProviderName.POLICYCENTER: "get_policy",
            ProviderName.EDW:          "get_customer_profile",
            ProviderName.DOCUMENTS:    "get_documents",
            ProviderName.FRAUD:        "get_fraud_indicators",
            ProviderName.EMAIL:        "get_claim_correspondence",
        }
        method_name = method_dispatch.get(provider_name, "unknown")

        try:
            provider = registry.resolve(provider_name)
        except IntegrationConfigError as exc:
            elapsed = (time.perf_counter() - t_start) * 1000
            traces.append(ProviderTrace(
                provider=provider_name,
                method=method_name,
                status="error",
                latency_ms=round(elapsed, 2),
                error_code="REGISTRY_ERROR",
                error_message=str(exc),
            ))
            logger.error("Supervisor: registry error for %s", provider_name)
            continue

        result, tag = _call_with_retry(intent, provider_name, provider, request.claim_id, ctx)
        elapsed = (time.perf_counter() - t_start) * 1000

        if result is None:
            traces.append(ProviderTrace(
                provider=provider_name,
                method=method_name,
                status="error",
                latency_ms=round(elapsed, 2),
                error_code="CALL_FAILED",
                error_message=f"Call failed after retries (tag={tag})",
            ))
            logger.warning("Supervisor: %s failed (tag=%s)", provider_name, tag)
            continue

        result_status = getattr(result, "status", None)
        status_str = result_status.value if hasattr(result_status, "value") else str(result_status)
        err = getattr(result, "error", None)

        traces.append(ProviderTrace(
            provider=provider_name,
            method=method_name,
            status=status_str,
            latency_ms=round(elapsed, 2),
            error_code=err.code if err else None,
            error_message=err.message if err else None,
            retryable=err.retryable if err else False,
        ))
        raw_results[provider_name] = result
        logger.debug("Supervisor: %s → %s in %.1fms", provider_name, status_str, elapsed)

    exec_ms = (time.perf_counter() - exec_start) * 1000

    # --- AGGREGATE ---
    agg_start = time.perf_counter()
    aggregated, overall_status = aggregate(intent, traces, raw_results)
    agg_ms = (time.perf_counter() - agg_start) * 1000

    total_ms = (time.perf_counter() - wall_start) * 1000

    succeeded = sum(1 for t in traces if t.status == "success")
    failed = len(traces) - succeeded

    logger.info(
        "Supervisor: END request_id=%s status=%s providers=%d/%d "
        "exec_ms=%.1f agg_ms=%.1f total_ms=%.1f",
        request_id, overall_status.value, succeeded, len(traces),
        exec_ms, agg_ms, total_ms,
    )

    return SupervisorResponse(
        request_id=request_id,
        intent=intent.value,
        selected_providers=providers_plan,
        execution_trace=traces,
        aggregated_result=aggregated,
        status=overall_status,
        governance_flags=GovernanceFlags(
            writes_enabled=False,
            provider_mode_enforced="mock",
            real_providers_rejected=True,
            all_operations_read_only=True,
            phase_2b_gate_open=False,
        ),
        latency_ms=round(total_ms, 2),
        provider_count=len(traces),
        succeeded_count=succeeded,
        failed_count=failed,
    )
