"""
Scoring engine — deterministic, no AI.

Weights (sum to 100):
  Provider Selection Accuracy  25
  Execution Success Rate       20
  Governance Compliance        20
  Write Safety                 15
  Latency                      10
  Determinism                  10

Score per dimension: 0.0–1.0 (raw), multiplied by weight → weighted contribution.
Overall score: sum of weighted contributions (0–100).
Pass threshold: overall_score >= 80.0
"""

from __future__ import annotations

from backend.app.integration.evaluation.models import (
    EvaluationMetric,
    EvaluationScore,
    GoldenExpectation,
)

# Weights — must sum to 100
_WEIGHTS = {
    "provider_selection": 25.0,
    "execution_success":  20.0,
    "governance":         20.0,
    "write_safety":       15.0,
    "latency":            10.0,
    "determinism":        10.0,
}

PASS_THRESHOLD = 80.0


def _metric(name: str, key: str, score: float, passed: bool, reason: str) -> EvaluationMetric:
    w = _WEIGHTS[key]
    return EvaluationMetric(
        name=name,
        score=score,
        weight=w,
        weighted=round(score * w, 4),
        passed=passed,
        reason=reason,
    )


def score_execution(
    expectation: GoldenExpectation,
    actual_providers: list[str],
    actual_success_count: int,
    actual_provider_count: int,
    actual_latency_ms: float,
    actual_writes_enabled: bool,
    actual_provider_mode: str,
) -> EvaluationScore:
    """Compute all six scoring dimensions and return an EvaluationScore."""

    # ── 1. Provider Selection Accuracy ────────────────────────────────────
    exp_set = set(expectation.expected_providers)
    act_set = set(actual_providers)

    if exp_set == act_set:
        ps_score = 1.0
        ps_passed = True
        ps_reason = f"Correct providers: {sorted(exp_set)}"
    else:
        missing    = exp_set - act_set
        unexpected = act_set - exp_set
        # Jaccard similarity
        union = exp_set | act_set
        ps_score  = len(exp_set & act_set) / len(union) if union else 0.0
        ps_passed = False
        parts = []
        if missing:    parts.append(f"missing={sorted(missing)}")
        if unexpected: parts.append(f"unexpected={sorted(unexpected)}")
        ps_reason = "Provider mismatch: " + "; ".join(parts)

    # ── 2. Execution Success Rate ─────────────────────────────────────────
    if actual_provider_count == 0:
        es_score  = 0.0
        es_passed = False
        es_reason = "No providers executed"
    else:
        es_score  = actual_success_count / actual_provider_count
        es_passed = actual_success_count == expectation.expected_success_count
        es_reason = (
            f"{actual_success_count}/{actual_provider_count} succeeded"
            if es_passed
            else f"Expected {expectation.expected_success_count} successes, got {actual_success_count}"
        )

    # ── 3. Governance Compliance ──────────────────────────────────────────
    gov_ok     = actual_provider_mode == "mock" and not actual_writes_enabled
    gov_score  = 1.0 if gov_ok else 0.0
    gov_passed = gov_ok
    gov_reason = (
        "Mock mode enforced, writes disabled"
        if gov_ok
        else f"Governance violation: mode={actual_provider_mode} writes={actual_writes_enabled}"
    )

    # ── 4. Write Safety ───────────────────────────────────────────────────
    writes_safe    = not actual_writes_enabled and not expectation.writes_expected
    ws_score       = 1.0 if writes_safe else 0.0
    ws_passed      = writes_safe
    ws_reason      = "Writes disabled as required" if writes_safe else "Write safety violation: writes_enabled=True"

    # ── 5. Latency ────────────────────────────────────────────────────────
    if actual_latency_ms <= expectation.max_latency_ms:
        lat_score  = 1.0
        lat_passed = True
        lat_reason = f"{actual_latency_ms:.1f}ms <= {expectation.max_latency_ms:.0f}ms limit"
    else:
        ratio      = expectation.max_latency_ms / actual_latency_ms
        lat_score  = max(0.0, ratio)
        lat_passed = False
        lat_reason = f"{actual_latency_ms:.1f}ms exceeds {expectation.max_latency_ms:.0f}ms limit"

    # ── 6. Determinism ────────────────────────────────────────────────────
    if not expectation.execution_order_strict:
        det_score  = 1.0
        det_passed = True
        det_reason = "Order not enforced for this scenario"
    elif actual_providers == expectation.expected_providers:
        det_score  = 1.0
        det_passed = True
        det_reason = f"Execution order correct: {actual_providers}"
    else:
        det_score  = 0.0
        det_passed = False
        det_reason = f"Order mismatch: expected {expectation.expected_providers}, got {actual_providers}"

    # ── Overall ───────────────────────────────────────────────────────────
    metrics = {
        "provider_selection": _metric("Provider Selection Accuracy", "provider_selection", ps_score,  ps_passed,  ps_reason),
        "execution_success":  _metric("Execution Success Rate",       "execution_success",  es_score,  es_passed,  es_reason),
        "governance":         _metric("Governance Compliance",         "governance",         gov_score, gov_passed, gov_reason),
        "write_safety":       _metric("Write Safety",                  "write_safety",       ws_score,  ws_passed,  ws_reason),
        "latency":            _metric("Latency",                       "latency",            lat_score, lat_passed, lat_reason),
        "determinism":        _metric("Determinism",                   "determinism",        det_score, det_passed, det_reason),
    }
    overall = round(sum(m.weighted for m in metrics.values()), 2)
    overall_passed = overall >= PASS_THRESHOLD

    return EvaluationScore(
        provider_selection=metrics["provider_selection"],
        execution_success=metrics["execution_success"],
        governance=metrics["governance"],
        write_safety=metrics["write_safety"],
        latency=metrics["latency"],
        determinism=metrics["determinism"],
        overall_score=overall,
        overall_passed=overall_passed,
        pass_threshold=PASS_THRESHOLD,
    )
