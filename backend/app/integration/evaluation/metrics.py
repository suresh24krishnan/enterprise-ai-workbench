"""
Regression detection engine.

Compares an actual supervisor response against a GoldenExpectation
and returns a list of RegressionResult objects (one per detected deviation).
"""

from __future__ import annotations

from backend.app.integration.evaluation.models import (
    GoldenExpectation,
    RegressionResult,
    RegressionType,
)


def detect_regressions(
    expectation: GoldenExpectation,
    actual_providers: list[str],
    actual_success_count: int,
    actual_provider_count: int,
    actual_latency_ms: float,
    actual_writes_enabled: bool,
    actual_provider_mode: str,
) -> list[RegressionResult]:
    """Return all regressions found; empty list means PASS."""
    results: list[RegressionResult] = []

    exp_set = set(expectation.expected_providers)
    act_set = set(actual_providers)

    # Missing providers
    for p in sorted(exp_set - act_set):
        results.append(RegressionResult(
            regression_type=RegressionType.MISSING_PROVIDER,
            severity="critical",
            detail=f"Provider '{p}' was expected but not selected",
            expected=expectation.expected_providers,
            actual=actual_providers,
        ))

    # Unexpected providers
    for p in sorted(act_set - exp_set):
        results.append(RegressionResult(
            regression_type=RegressionType.UNEXPECTED_PROVIDER,
            severity="warning",
            detail=f"Provider '{p}' was not expected but was selected",
            expected=expectation.expected_providers,
            actual=actual_providers,
        ))

    # Provider failures (success count less than expected)
    if actual_success_count < expectation.expected_success_count:
        results.append(RegressionResult(
            regression_type=RegressionType.PROVIDER_FAILURE,
            severity="critical",
            detail=f"Expected {expectation.expected_success_count} successes, got {actual_success_count}",
            expected=expectation.expected_success_count,
            actual=actual_success_count,
        ))

    # Write enabled when it should not be
    if actual_writes_enabled and not expectation.writes_expected:
        results.append(RegressionResult(
            regression_type=RegressionType.WRITE_ENABLED,
            severity="critical",
            detail="Writes are enabled but writes_expected=False for this scenario",
            expected=False,
            actual=True,
        ))

    # Real provider when mock expected
    if actual_provider_mode != "mock" and not expectation.real_providers_expected:
        results.append(RegressionResult(
            regression_type=RegressionType.REAL_PROVIDER_ENABLED,
            severity="critical",
            detail=f"provider_mode='{actual_provider_mode}' but real_providers_expected=False",
            expected="mock",
            actual=actual_provider_mode,
        ))

    # Latency exceeded
    if actual_latency_ms > expectation.max_latency_ms:
        results.append(RegressionResult(
            regression_type=RegressionType.LATENCY_EXCEEDED,
            severity="warning",
            detail=f"Latency {actual_latency_ms:.1f}ms exceeds limit {expectation.max_latency_ms:.0f}ms",
            expected=expectation.max_latency_ms,
            actual=actual_latency_ms,
        ))

    # Execution order mismatch
    if (
        expectation.execution_order_strict
        and actual_providers != expectation.expected_providers
        and act_set == exp_set  # same set, wrong order only
    ):
        results.append(RegressionResult(
            regression_type=RegressionType.WRONG_EXECUTION_ORDER,
            severity="warning",
            detail="Providers selected correctly but in unexpected order",
            expected=expectation.expected_providers,
            actual=actual_providers,
        ))

    # Wrong provider count
    if actual_provider_count != expectation.expected_provider_count:
        results.append(RegressionResult(
            regression_type=RegressionType.WRONG_PROVIDER_COUNT,
            severity="critical",
            detail=f"Expected {expectation.expected_provider_count} providers, got {actual_provider_count}",
            expected=expectation.expected_provider_count,
            actual=actual_provider_count,
        ))

    # Wrong success count (separate from provider failure — catches partial when full expected)
    if (
        actual_success_count != expectation.expected_success_count
        and actual_success_count >= expectation.expected_success_count
    ):
        results.append(RegressionResult(
            regression_type=RegressionType.WRONG_SUCCESS_COUNT,
            severity="warning",
            detail=f"Success count {actual_success_count} differs from expected {expectation.expected_success_count}",
            expected=expectation.expected_success_count,
            actual=actual_success_count,
        ))

    return results
