"""
Control Tower API — observability endpoints for supervised executions.

Exposes:
  GET /api/integration/control-tower/runs           — recent run summaries
  GET /api/integration/control-tower/runs/{id}      — full run detail
  GET /api/integration/control-tower/summary        — aggregate statistics

Security:
  - Read-only. No state mutations.
  - No secrets, tokens, or credentials in any response.
  - No document body text or email body text.
  - Governance flags always reflect writes_enabled=False.

This endpoint is additive — does not touch any Sprint 0–5 route or behaviour.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.app.integration.control_tower import service as ct_service
from backend.app.integration.control_tower.models import (
    ControlTowerRun,
    ControlTowerRunSummary,
    ControlTowerSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integration/control-tower", tags=["control-tower"])


@router.get("/runs", response_model=list[ControlTowerRunSummary])
def get_runs(limit: int = 25) -> list[ControlTowerRunSummary]:
    """
    Return recent supervisor run summaries, newest first.

    Each entry contains: request_id, intent, status, provider_count,
    succeeded_count, failed_count, latency_ms, writes_enabled, provider_mode.

    No document or email body content is included.
    """
    if limit < 1 or limit > 25:
        limit = 25
    return ct_service.get_run_summaries(limit=limit)


@router.get("/runs/{request_id}", response_model=ControlTowerRun)
def get_run_detail(request_id: str) -> ControlTowerRun:
    """
    Return the full Control Tower record for a single supervisor run.

    Includes per-provider execution steps with latency and status,
    governance summary, and timing. No document or email body content.
    """
    run = ct_service.get_run_detail(request_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{request_id}' not found. "
                   f"Runs are stored in-memory and cleared on restart.",
        )
    return run


@router.get("/summary", response_model=ControlTowerSummary)
def get_summary() -> ControlTowerSummary:
    """
    Return aggregate statistics across all stored runs.

    Includes: total_runs, success/partial/failed counts, average_latency_ms,
    writes_enabled (always False), lab_safe (always True), provider_modes.
    """
    return ct_service.get_summary()
