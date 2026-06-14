"""
Report builder — assembles a human-readable EvaluationResult from raw components.

JSON-serializable via .model_dump().
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.app.integration.evaluation.models import (
    EvalStatus,
    EvaluationResult,
    EvaluationScore,
    GoldenExpectation,
    GoldenScenario,
    RegressionResult,
)


def build_report(
    run_id: str,
    scenario: GoldenScenario,
    actual_providers: list[str],
    actual_provider_count: int,
    actual_success_count: int,
    actual_latency_ms: float,
    actual_status: str,
    actual_writes_enabled: bool,
    actual_provider_mode: str,
    score: EvaluationScore,
    regressions: list[RegressionResult],
) -> EvaluationResult:
    """Compose all evaluation components into a final EvaluationResult."""

    passed = score.overall_passed and not any(
        r.severity == "critical" for r in regressions
    )

    if passed:
        status = EvalStatus.PASS
        reason = f"All checks passed — score {score.overall_score:.1f}/100"
    else:
        status = EvalStatus.FAIL
        critical = [r for r in regressions if r.severity == "critical"]
        if critical:
            reason = f"Critical regressions: {[r.regression_type.value for r in critical]}"
        else:
            reason = f"Score {score.overall_score:.1f} below threshold {score.pass_threshold:.0f}"

    return EvaluationResult(
        run_id=run_id,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        claim_id=scenario.claim_id,
        intent=scenario.intent,
        expectation=scenario.expectation,
        actual_providers=actual_providers,
        actual_provider_count=actual_provider_count,
        actual_success_count=actual_success_count,
        actual_latency_ms=actual_latency_ms,
        actual_status=actual_status,
        actual_writes_enabled=actual_writes_enabled,
        actual_provider_mode=actual_provider_mode,
        score=score,
        regressions=regressions,
        status=status,
        passed=passed,
        reason=reason,
        recorded_at=datetime.now(timezone.utc).isoformat(),
        version=scenario.version,
    )


def build_recommendation(result: EvaluationResult) -> str:
    """One-line promotion recommendation based on result."""
    if result.passed:
        return "PROMOTE — All quality gates satisfied. Safe for Phase 2B promotion."
    critical = [r for r in result.regressions if r.severity == "critical"]
    if critical:
        types = ", ".join(r.regression_type.value for r in critical)
        return f"BLOCK — Critical regressions detected: {types}. Do not promote."
    return f"REVIEW — Score {result.score.overall_score:.1f}/100 below threshold. Investigate before promoting."
