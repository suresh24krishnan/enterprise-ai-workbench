"""
Evaluation API — Phase 2 Sprint 7

GET  /api/integration/evaluation/scenarios
POST /api/integration/evaluation/run
GET  /api/integration/evaluation/report/{run_id}
GET  /api/integration/evaluation/summary

Read-only. Writes remain disabled.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.app.integration.bootstrap import get_registry
from backend.app.integration.evaluation.golden_dataset import list_scenarios
from backend.app.integration.evaluation.models import (
    EvaluationRequest,
    EvaluationResult,
    EvaluationRun,
    EvaluationSummary,
    GoldenScenario,
)
from backend.app.integration.evaluation import runner as eval_runner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integration/evaluation", tags=["evaluation"])


@router.get("/scenarios", response_model=list[GoldenScenario])
def get_scenarios() -> list[GoldenScenario]:
    """Return all available golden scenarios."""
    return list_scenarios()


@router.post("/run", response_model=EvaluationResult)
def run_evaluation(request: EvaluationRequest) -> EvaluationResult:
    """
    Run one golden scenario through the supervisor and return a scored result.
    Does NOT modify any provider logic or write any data.
    """
    registry = get_registry()
    try:
        result = eval_runner.run_scenario(request.scenario_id, registry)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("evaluation run failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Evaluation error: {exc}")
    return result


@router.get("/report/{run_id}", response_model=EvaluationResult)
def get_report(run_id: str) -> EvaluationResult:
    """Return the full evaluation result for a specific run_id."""
    result = eval_runner.get_result(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return result


@router.get("/summary", response_model=EvaluationSummary)
def get_summary() -> EvaluationSummary:
    """Return aggregate statistics across all evaluation runs."""
    return eval_runner.get_summary()


@router.get("/runs", response_model=list[EvaluationRun])
def get_runs(limit: int = 50) -> list[EvaluationRun]:
    """Return recent evaluation runs, newest first."""
    return eval_runner.get_recent_runs(limit=min(limit, 50))


@router.get("/report/{run_id}/recommendation", response_model=dict)
def get_recommendation(run_id: str) -> dict:
    """Return the promotion recommendation for a run."""
    rec = eval_runner.get_recommendation(run_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return {"run_id": run_id, "recommendation": rec}
