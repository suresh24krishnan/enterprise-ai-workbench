"""
Executor — calls provider methods via the registry and records traces.

Rules:
  - All providers are resolved through the registry. No direct instantiation.
  - All calls are READ-ONLY. Write methods are never invoked here.
  - Failures are recorded in the trace; they never propagate past this module.
  - Retry is mock-safe only: one retry on retryable mock errors (timeout,
    unavailable). No infinite loops. No exponential backoff in mock mode.
  - The executor is intentionally provider-agnostic: it calls the same
    method name on every provider and lets the provider decide what to return.

Per-intent method dispatch:

  Each provider exposes a "primary read" method that the executor calls
  for a given (intent, provider) combination. The dispatch table below is
  static — there is no runtime method selection.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from backend.app.integration.contracts.common import (
    PaginationRequest,
    ProviderMode,
    ToolExecutionContext,
    ToolResultStatus,
)
from backend.app.integration.mocks.errors import (
    MockIntegrationError,
    MockTimeoutError,
    MockUnavailableError,
)
from backend.app.integration.modes import ProviderMode
from backend.app.integration.providers import ProviderName
from backend.app.integration.registry import IntegrationConfigError, ProviderRegistry

from .models import ClaimIntent, ProviderTrace

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static dispatch: (intent, provider) → method name + kwargs builder
# ---------------------------------------------------------------------------

def _make_context(claim_id: str) -> ToolExecutionContext:
    """Build a read-only execution context for the supervisor."""
    import uuid
    return ToolExecutionContext(
        user_id="supervisor",
        display_name="Claim Intelligence Supervisor",
        roles=["supervisor"],
        permissions=["read"],
        correlation_id=f"sup-{claim_id}",
        trace_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        provider_mode=ProviderMode.MOCK,
        writes_enabled=False,  # NEVER True in supervisor
    )


def _dispatch_call(
    intent: ClaimIntent,
    provider_name: str,
    provider: Any,
    claim_id: str,
    ctx: ToolExecutionContext,
) -> Any:
    """
    Call the appropriate read method on a provider for a given intent.

    Returns the raw ToolResult from the provider. Never raises — if the
    call fails, the exception is caught by execute_plan.
    """
    # ClaimCenter
    if provider_name == ProviderName.CLAIMCENTER:
        return provider.get_claim(claim_id, ctx)

    # PolicyCenter — resolve by policy number embedded in claim context
    # For now we use the well-known mock policy number; real adapters will
    # look up the policy ID from the claim detail first.
    if provider_name == ProviderName.POLICYCENTER:
        return provider.get_policy("CA-2024-8812", ctx)

    # EDW — customer profile
    if provider_name == ProviderName.EDW:
        return provider.get_customer_profile("EDW-CUST-10042", ctx)

    # Documents
    if provider_name == ProviderName.DOCUMENTS:
        return provider.get_documents(claim_id, ctx)

    # Fraud
    if provider_name == ProviderName.FRAUD:
        return provider.get_fraud_indicators(claim_id, ctx)

    # Email
    if provider_name == ProviderName.EMAIL:
        return provider.get_claim_correspondence(claim_id, ctx)

    raise ValueError(f"No dispatch rule for provider '{provider_name}'")


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

_MAX_RETRIES = 1  # one retry for retryable mock errors only


def _call_with_retry(
    intent: ClaimIntent,
    provider_name: str,
    provider: Any,
    claim_id: str,
    ctx: ToolExecutionContext,
) -> tuple[Any, str]:
    """
    Call the provider with one retry on retryable mock errors.

    Returns (result_or_None, "ok" | "retried_ok" | "retried_fail" | "error").
    """
    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = _dispatch_call(intent, provider_name, provider, claim_id, ctx)
            tag = "ok" if attempt == 0 else "retried_ok"
            return result, tag
        except (MockTimeoutError, MockUnavailableError) as exc:
            if attempt < _MAX_RETRIES and exc.retryable:
                logger.debug(
                    "Supervisor: retrying %s after %s (attempt %d)",
                    provider_name, type(exc).__name__, attempt + 1,
                )
                continue
            return None, "retried_fail"
        except MockIntegrationError:
            return None, "error"
        except Exception as exc:
            logger.warning(
                "Supervisor: unexpected error from %s: %s: %s",
                provider_name, type(exc).__name__, exc,
            )
            return None, "error"
    return None, "error"


def execute_plan(
    intent: ClaimIntent,
    providers_plan: list[str],
    registry: ProviderRegistry,
    claim_id: str,
) -> list[ProviderTrace]:
    """
    Execute a provider plan and return a list of execution traces.

    Every provider call is traced regardless of outcome. Failures in one
    provider never abort the remaining providers.

    Args:
        intent:         The resolved ClaimIntent.
        providers_plan: Ordered list of provider names from the planner.
        registry:       The application registry (sole source of providers).
        claim_id:       Claim ID to pass to each provider call.

    Returns:
        List of ProviderTrace — one entry per provider in the plan.
    """
    ctx = _make_context(claim_id)
    traces: list[ProviderTrace] = []

    for provider_name in providers_plan:
        start = time.perf_counter()

        # Resolve provider from registry — never instantiate directly
        try:
            provider = registry.resolve(provider_name)
        except IntegrationConfigError as exc:
            elapsed = (time.perf_counter() - start) * 1000
            traces.append(ProviderTrace(
                provider=provider_name,
                method="resolve",
                status="error",
                latency_ms=round(elapsed, 2),
                error_code="REGISTRY_ERROR",
                error_message=str(exc),
                retryable=False,
            ))
            logger.error("Supervisor: registry error for %s: %s", provider_name, exc)
            continue

        # Determine method name for tracing
        method_dispatch = {
            ProviderName.CLAIMCENTER:  "get_claim",
            ProviderName.POLICYCENTER: "get_policy",
            ProviderName.EDW:          "get_customer_profile",
            ProviderName.DOCUMENTS:    "get_documents",
            ProviderName.FRAUD:        "get_fraud_indicators",
            ProviderName.EMAIL:        "get_claim_correspondence",
        }
        method_name = method_dispatch.get(provider_name, "unknown")

        result, tag = _call_with_retry(intent, provider_name, provider, claim_id, ctx)
        elapsed = (time.perf_counter() - start) * 1000

        if result is None:
            traces.append(ProviderTrace(
                provider=provider_name,
                method=method_name,
                status="error",
                latency_ms=round(elapsed, 2),
                error_code="CALL_FAILED",
                error_message=f"Provider call failed after retries (tag={tag})",
                retryable=False,
            ))
            logger.warning(
                "Supervisor: %s.%s failed (tag=%s) in %.1fms",
                provider_name, method_name, tag, elapsed,
            )
            continue

        # Inspect result status
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
        logger.debug(
            "Supervisor: %s.%s → %s in %.1fms",
            provider_name, method_name, status_str, elapsed,
        )

    return traces
