"""
Supervisor endpoint — POST /api/integration/supervisor/run

Executes a deterministic claim intelligence request through the supervisor
pipeline: classify intent → select providers → enforce governance → execute
read-only provider calls → aggregate → return structured response.

SAFETY:
  - READ ONLY. No provider write methods are called.
  - No side effects outside mock provider execution.
  - No UI changes. No frontend dependency.
  - Governance constraints enforced before any provider call.
  - Returns 422 if governance is violated (e.g. REAL provider configured).

This endpoint is additive — it does not modify any existing route,
API contract, or application behaviour from Sprints 0–4.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.app.integration.bootstrap import get_registry
from backend.app.integration.registry import IntegrationConfigError
from backend.app.integration.supervisor.models import SupervisorRequest, SupervisorResponse
from backend.app.integration.supervisor.supervisor import run_supervisor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integration/supervisor", tags=["supervisor"])


@router.post("/run", response_model=SupervisorResponse)
def supervisor_run(request: SupervisorRequest) -> SupervisorResponse:
    """
    Execute a claim intelligence request.

    Input:
        claim_id  — The claim to fetch intelligence for.
        intent    — Processing intent (claim_summary, coverage_analysis,
                    fraud_check, document_review, policy_lookup).
                    Defaults to claim_summary.
        context   — Optional caller context (not used to change governance).

    Output:
        SupervisorResponse with execution trace, aggregated result,
        governance flags, and timing.

    Errors:
        422 — Governance violation (e.g. REAL provider configured).
        500 — Unexpected supervisor error.
    """
    registry = get_registry()
    try:
        return run_supervisor(request, registry)
    except IntegrationConfigError as exc:
        logger.warning("Supervisor endpoint: governance violation — %s", exc)
        raise HTTPException(
            status_code=422,
            detail=f"Governance violation: {exc}",
        )
    except Exception as exc:
        logger.error("Supervisor endpoint: unexpected error — %s: %s", type(exc).__name__, exc)
        raise HTTPException(
            status_code=500,
            detail="Supervisor execution failed. See server logs.",
        )
