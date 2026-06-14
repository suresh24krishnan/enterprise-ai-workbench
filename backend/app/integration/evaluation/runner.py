"""
Evaluation runner — orchestrates one golden scenario through the supervisor.

Execution model:
  GoldenScenario
    ↓ build SupervisorRequest
    ↓ run_supervisor()
    ↓ collect response
    ↓ score_execution()
    ↓ detect_regressions()
    ↓ build_report()
    ↓ store in eval_store
    ↓ return EvaluationResult

No frontend dependency. Pure backend. Writes remain disabled.
"""

from __future__ import annotations

import uuid
import logging

from backend.app.integration.evaluation.golden_dataset import get_scenario, list_scenarios
from backend.app.integration.evaluation.metrics import detect_regressions
from backend.app.integration.evaluation.models import (
    EvaluationResult,
    EvaluationRun,
    EvaluationSummary,
)
from backend.app.integration.evaluation.report import build_report, build_recommendation
from backend.app.integration.evaluation.scoring import score_execution
from backend.app.integration.supervisor.models import SupervisorRequest
from backend.app.integration.supervisor.supervisor import run_supervisor

logger = logging.getLogger(__name__)


# ── In-memory store (identical pattern to Control Tower) ──────────────────

from collections import deque
import threading

_MAX_RESULTS = 50
_store: deque[EvaluationResult] = deque(maxlen=_MAX_RESULTS)
_lock = threading.Lock()


def _store_result(result: EvaluationResult) -> None:
    with _lock:
        _store.append(result)


def get_result(run_id: str) -> EvaluationResult | None:
    with _lock:
        for r in _store:
            if r.run_id == run_id:
                return r
    return None


def get_recent_runs(limit: int = 50) -> list[EvaluationRun]:
    with _lock:
        results = list(_store)
    results.reverse()
    runs = [
        EvaluationRun(
            run_id=r.run_id,
            scenario_id=r.scenario_id,
            scenario_name=r.scenario_name,
            claim_id=r.claim_id,
            intent=r.intent,
            overall_score=r.score.overall_score,
            passed=r.passed,
            regression_count=len(r.regressions),
            latency_ms=r.actual_latency_ms,
            recorded_at=r.recorded_at,
        )
        for r in results
    ]
    return runs[:limit]


def get_summary() -> EvaluationSummary:
    with _lock:
        results = list(_store)
    if not results:
        return EvaluationSummary(
            total_runs=0, pass_count=0, fail_count=0,
            pass_rate=0.0, average_score=0.0, regression_count=0,
            last_run_at=None, last_run_id=None,
            store_used=0, store_capacity=_MAX_RESULTS,
        )
    pass_count  = sum(1 for r in results if r.passed)
    fail_count  = len(results) - pass_count
    avg_score   = sum(r.score.overall_score for r in results) / len(results)
    reg_count   = sum(len(r.regressions) for r in results)
    last        = results[-1]
    return EvaluationSummary(
        total_runs=len(results),
        pass_count=pass_count,
        fail_count=fail_count,
        pass_rate=round(pass_count / len(results), 4),
        average_score=round(avg_score, 2),
        regression_count=reg_count,
        last_run_at=last.recorded_at,
        last_run_id=last.run_id,
        store_used=len(results),
        store_capacity=_MAX_RESULTS,
    )


def store_capacity() -> int:
    return _MAX_RESULTS


def store_size() -> int:
    with _lock:
        return len(_store)


# ── Runner ─────────────────────────────────────────────────────────────────


def run_scenario(scenario_id: str, registry) -> EvaluationResult:
    """
    Run one golden scenario through the supervisor and return a scored result.
    Raises ValueError if scenario_id is unknown.
    """
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    run_id = str(uuid.uuid4())
    logger.info("eval: running scenario=%s run_id=%s", scenario_id, run_id)

    req = SupervisorRequest(claim_id=scenario.claim_id, intent=scenario.intent)
    resp = run_supervisor(req, registry)

    actual_providers     = resp.selected_providers
    actual_provider_count = resp.provider_count
    actual_success_count  = resp.succeeded_count
    actual_latency_ms     = resp.latency_ms
    actual_status         = resp.status.value
    actual_writes_enabled = resp.governance_flags.writes_enabled
    actual_provider_mode  = resp.governance_flags.provider_mode_enforced

    score = score_execution(
        expectation=scenario.expectation,
        actual_providers=actual_providers,
        actual_success_count=actual_success_count,
        actual_provider_count=actual_provider_count,
        actual_latency_ms=actual_latency_ms,
        actual_writes_enabled=actual_writes_enabled,
        actual_provider_mode=actual_provider_mode,
    )

    regressions = detect_regressions(
        expectation=scenario.expectation,
        actual_providers=actual_providers,
        actual_success_count=actual_success_count,
        actual_provider_count=actual_provider_count,
        actual_latency_ms=actual_latency_ms,
        actual_writes_enabled=actual_writes_enabled,
        actual_provider_mode=actual_provider_mode,
    )

    result = build_report(
        run_id=run_id,
        scenario=scenario,
        actual_providers=actual_providers,
        actual_provider_count=actual_provider_count,
        actual_success_count=actual_success_count,
        actual_latency_ms=actual_latency_ms,
        actual_status=actual_status,
        actual_writes_enabled=actual_writes_enabled,
        actual_provider_mode=actual_provider_mode,
        score=score,
        regressions=regressions,
    )

    _store_result(result)
    logger.info(
        "eval: scenario=%s run_id=%s status=%s score=%.1f regressions=%d",
        scenario_id, run_id, result.status.value, score.overall_score, len(regressions),
    )
    return result


def run_all_scenarios(registry) -> list[EvaluationResult]:
    """Run every golden scenario and return results in order."""
    results = []
    for scenario in list_scenarios():
        try:
            result = run_scenario(scenario.scenario_id, registry)
        except Exception as exc:
            logger.error("eval: scenario=%s failed with %s", scenario.scenario_id, exc)
            continue
        results.append(result)
    return results


def get_recommendation(run_id: str) -> str | None:
    result = get_result(run_id)
    if result is None:
        return None
    return build_recommendation(result)
