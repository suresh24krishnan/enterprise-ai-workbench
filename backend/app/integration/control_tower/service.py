"""
Control Tower service — converts SupervisorResponse into ControlTowerRun.

This is the only module that touches SupervisorResponse. All other Control
Tower modules work with ControlTowerRun exclusively.

Security:
  - Email body text is not extracted (it lives in aggregated_result which
    is not copied here — only trace metadata is captured).
  - Document content is not extracted.
  - No secrets from the execution context are stored.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.app.integration.supervisor.models import SupervisorResponse

from .models import (
    ControlTowerGovernanceSummary,
    ControlTowerProviderStep,
    ControlTowerRun,
    ControlTowerRunSummary,
    ControlTowerSummary,
)
from . import trace_store


def record_supervisor_response(
    claim_id: str,
    response: SupervisorResponse,
) -> ControlTowerRun:
    """
    Convert a SupervisorResponse into a ControlTowerRun and record it.

    Only metadata is captured — no aggregated_result, no document/email bodies.

    Args:
        claim_id:  The claim ID from the original request.
        response:  The completed SupervisorResponse.

    Returns:
        The recorded ControlTowerRun.
    """
    steps = [
        ControlTowerProviderStep(
            provider=t.provider,
            method=t.method,
            status=t.status,
            latency_ms=t.latency_ms,
            retryable=t.retryable,
            error_code=t.error_code,
            error_message=t.error_message,
        )
        for t in response.execution_trace
    ]

    gf = response.governance_flags
    governance = ControlTowerGovernanceSummary(
        writes_enabled=gf.writes_enabled,
        provider_mode_enforced=gf.provider_mode_enforced,
        real_providers_rejected=gf.real_providers_rejected,
        all_operations_read_only=gf.all_operations_read_only,
        phase_2b_gate_open=gf.phase_2b_gate_open,
    )

    run = ControlTowerRun(
        request_id=response.request_id,
        claim_id=claim_id,
        intent=response.intent,
        selected_providers=response.selected_providers,
        steps=steps,
        governance=governance,
        status=response.status.value,
        latency_ms=response.latency_ms,
        provider_count=response.provider_count,
        succeeded_count=response.succeeded_count,
        failed_count=response.failed_count,
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )

    trace_store.record_run(run)
    return run


def get_run_summaries(limit: int = 25) -> list[ControlTowerRunSummary]:
    """Return lightweight summaries for the runs list endpoint."""
    runs = trace_store.get_runs(limit=limit)
    return [
        ControlTowerRunSummary(
            request_id=r.request_id,
            claim_id=r.claim_id,
            intent=r.intent,
            status=r.status,
            provider_count=r.provider_count,
            succeeded_count=r.succeeded_count,
            failed_count=r.failed_count,
            latency_ms=r.latency_ms,
            writes_enabled=r.governance.writes_enabled,
            provider_mode=r.governance.provider_mode_enforced,
            recorded_at=r.recorded_at,
        )
        for r in runs
    ]


def get_run_detail(request_id: str) -> ControlTowerRun | None:
    """Return the full ControlTowerRun for a request_id, or None."""
    return trace_store.get_run(request_id)


def get_summary() -> ControlTowerSummary:
    """Return aggregate statistics across all stored runs."""
    runs = trace_store.get_runs(limit=trace_store.store_capacity())

    total = len(runs)
    success = sum(1 for r in runs if r.status == "success")
    partial = sum(1 for r in runs if r.status == "partial")
    failed = sum(1 for r in runs if r.status == "failed")
    avg_latency = (
        round(sum(r.latency_ms for r in runs) / total, 2) if total > 0 else 0.0
    )
    modes = sorted({r.governance.provider_mode_enforced for r in runs}) if runs else ["mock"]

    return ControlTowerSummary(
        total_runs=total,
        success_count=success,
        partial_count=partial,
        failed_count=failed,
        average_latency_ms=avg_latency,
        writes_enabled=False,   # structural invariant — never True in Phase 2A
        lab_safe=True,
        provider_modes=modes if modes else ["mock"],
        store_capacity=trace_store.store_capacity(),
        store_used=trace_store.store_size(),
    )
