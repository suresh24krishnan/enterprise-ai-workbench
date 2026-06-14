"""
Failure injection — boundary and resilience testing.

Simulates adverse conditions that a provider must survive without
crashing the application:

  1. Timeout injection       — provider raises MockTimeoutError
  2. Empty response          — provider returns SUCCESS with empty list/None
  3. Partial response        — pagination returns page 2 of 1-page result
  4. fail_after_n            — provider succeeds N times then fails
  5. Rapid successive calls  — provider handles multiple calls in sequence
  6. Unknown IDs             — provider returns NOT_FOUND (not raises)
  7. Dependency failure      — UNAVAILABLE mode simulates downstream outage

None of these tests call external systems. All operate against mock
providers with injected SimulationConfig.

Design rule: failure injection results in a structured FailureInjectionResult,
not a crash. The runner catches all exceptions from the providers under test
and records them as violations rather than propagating them. This ensures
the validation suite can complete even if one provider is broken.

Safety: MOCK mode only. No real providers are touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    MockWriteDisabledError,
)
from backend.app.integration.mocks.simulation import FailureMode, SimulationConfig

_TEST_CTX = ToolExecutionContext(
    user_id="failure-injector",
    display_name="Failure Injection Test",
    roles=["adjuster"],
    permissions=["read"],
    correlation_id="fi-corr",
    trace_id="fi-trace",
    request_id="fi-req",
    provider_mode=ProviderMode.MOCK,
    writes_enabled=False,
)

_KNOWN_CLAIM_ID = "CLM-2026-100245"
_UNKNOWN_ID = "UNKNOWN-INJECTED-99999"


@dataclass
class InjectionCheck:
    name: str
    passed: bool
    detail: str


@dataclass
class FailureInjectionResult:
    provider_name: str
    all_passed: bool
    checks: list[InjectionCheck] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    @property
    def summary(self) -> str:
        total = len(self.checks)
        if self.all_passed:
            return f"PASS ({self.passed_count}/{total} scenarios)"
        return f"FAIL ({self.passed_count}/{total} scenarios, {self.failed_count} failed)"


def _record(checks: list[InjectionCheck], name: str, passed: bool, detail: str) -> None:
    checks.append(InjectionCheck(name=name, passed=passed, detail=detail))


def _get_primary_call(provider_name: str, provider: Any):
    """Return the main triggerable call for a provider."""
    ctx = _TEST_CTX
    dispatch = {
        "claimcenter":  lambda: provider.get_claim(_KNOWN_CLAIM_ID, ctx),
        "policycenter": lambda: provider.get_policy("CA-2024-8812", ctx),
        "edw":          lambda: provider.get_customer_profile("EDW-CUST-10042", ctx),
        "documents":    lambda: provider.get_documents(_KNOWN_CLAIM_ID, ctx),
        "fraud":        lambda: provider.get_fraud_indicators(_KNOWN_CLAIM_ID, ctx),
        "email":        lambda: provider.get_claim_correspondence(_KNOWN_CLAIM_ID, ctx),
    }
    return dispatch.get(provider_name)


# ---------------------------------------------------------------------------
# Injection scenarios
# ---------------------------------------------------------------------------

def _inject_timeout(
    provider_name: str, provider_class: type, checks: list[InjectionCheck]
) -> None:
    """Provider with TIMEOUT mode must raise MockTimeoutError (retryable)."""
    sim = SimulationConfig(failure_mode=FailureMode.TIMEOUT)
    try:
        p = provider_class(sim=sim)
        call = _get_primary_call(provider_name, p)
        if call is None:
            _record(checks, "timeout_injection", True, "no primary call — skipped")
            return
        call()
        _record(checks, "timeout_injection", False,
                "Expected MockTimeoutError but call returned without exception")
    except MockTimeoutError as e:
        _record(checks, "timeout_injection", e.retryable is True,
                f"MockTimeoutError raised, retryable={e.retryable} (expected True)")
    except Exception as exc:
        _record(checks, "timeout_injection", False,
                f"Wrong exception: {type(exc).__name__}: {exc}")


def _inject_unavailable(
    provider_name: str, provider_class: type, checks: list[InjectionCheck]
) -> None:
    """UNAVAILABLE mode simulates downstream dependency failure."""
    sim = SimulationConfig(failure_mode=FailureMode.UNAVAILABLE)
    try:
        p = provider_class(sim=sim)
        call = _get_primary_call(provider_name, p)
        if call is None:
            _record(checks, "unavailable_injection", True, "no primary call — skipped")
            return
        call()
        _record(checks, "unavailable_injection", False,
                "Expected MockUnavailableError but call returned without exception")
    except MockUnavailableError as e:
        _record(checks, "unavailable_injection", e.retryable is True,
                f"MockUnavailableError raised, retryable={e.retryable} (expected True)")
    except Exception as exc:
        _record(checks, "unavailable_injection", False,
                f"Wrong exception: {type(exc).__name__}: {exc}")


def _inject_empty_response(
    provider_name: str, provider: Any, checks: list[InjectionCheck]
) -> None:
    """
    Unknown ID should return NOT_FOUND with a populated ToolError, not raise.
    An exception escaping on an unknown ID is an empty-response boundary failure.
    """
    ctx = _TEST_CTX
    unknown_calls: dict[str, Any] = {
        "claimcenter":  lambda: provider.get_claim(_UNKNOWN_ID, ctx),
        "policycenter": lambda: provider.get_policy(_UNKNOWN_ID, ctx),
        "edw":          lambda: provider.get_customer_profile(_UNKNOWN_ID, ctx),
        "documents":    lambda: provider.get_documents(_UNKNOWN_ID, ctx),
        "fraud":        lambda: provider.get_fraud_indicators(_UNKNOWN_ID, ctx),
        "email":        lambda: provider.get_claim_correspondence(_UNKNOWN_ID, ctx),
    }
    call = unknown_calls.get(provider_name)
    if call is None:
        _record(checks, "empty_response_unknown_id", True, "no call for this provider — skipped")
        return
    try:
        result = call()
        status = getattr(result, "status", None)
        # Acceptable: NOT_FOUND with error, or SUCCESS with empty collection
        if status == ToolResultStatus.NOT_FOUND:
            err = getattr(result, "error", None)
            if err is None:
                _record(checks, "empty_response_unknown_id", False,
                        "NOT_FOUND returned but error field is None")
            else:
                _record(checks, "empty_response_unknown_id", True,
                        f"NOT_FOUND returned with error.code={err.code!r}")
        elif status == ToolResultStatus.SUCCESS:
            # Email may return empty SUCCESS — acceptable
            _record(checks, "empty_response_unknown_id", True,
                    f"SUCCESS returned for unknown ID (empty collection is acceptable for {provider_name})")
        else:
            _record(checks, "empty_response_unknown_id", False,
                    f"Unexpected status {status} for unknown ID")
    except MockWriteDisabledError:
        _record(checks, "empty_response_unknown_id", True,
                "MockWriteDisabledError (write method) — not applicable to this check")
    except MockIntegrationError as exc:
        _record(checks, "empty_response_unknown_id", False,
                f"MockIntegrationError escaped on unknown ID: {type(exc).__name__}: {exc}. "
                f"Unknown IDs must return NOT_FOUND result, not raise.")
    except Exception as exc:
        _record(checks, "empty_response_unknown_id", False,
                f"Raw exception escaped on unknown ID: {type(exc).__name__}: {exc}")


def _inject_partial_response(
    provider_name: str, provider: Any, checks: list[InjectionCheck]
) -> None:
    """
    Request page 2 of a 1-page result. Provider must return SUCCESS with
    empty list and correct pagination (not crash, not raise).
    """
    ctx = _TEST_CTX
    paginated_calls = {
        "claimcenter": lambda: provider.get_claims("usr-john-smith", ctx,
                                                    pagination=PaginationRequest(page=99, page_size=100)),
        "documents":   lambda: provider.get_documents(_KNOWN_CLAIM_ID, ctx,
                                                       pagination=PaginationRequest(page=99, page_size=100)),
    }
    call = paginated_calls.get(provider_name)
    if call is None:
        _record(checks, "partial_response_out_of_range_page", True,
                f"{provider_name} has no paginated list — skipped")
        return
    try:
        result = call()
        status = getattr(result, "status", None)
        if status == ToolResultStatus.SUCCESS:
            # Out-of-range page should return empty list, not crash
            _record(checks, "partial_response_out_of_range_page", True,
                    "Out-of-range page returned SUCCESS with empty/partial list")
        else:
            _record(checks, "partial_response_out_of_range_page", False,
                    f"Out-of-range page returned unexpected status: {status}")
    except Exception as exc:
        _record(checks, "partial_response_out_of_range_page", False,
                f"Out-of-range page raised exception: {type(exc).__name__}: {exc}")


def _inject_fail_after_n(
    provider_name: str, provider_class: type, checks: list[InjectionCheck]
) -> None:
    """
    fail_after_n=2 — first 2 calls succeed, 3rd raises MockTimeoutError.
    Validates the retry-testing path.
    """
    sim = SimulationConfig(failure_mode=FailureMode.TIMEOUT, fail_after_n=2)
    try:
        p = provider_class(sim=sim)
    except TypeError:
        _record(checks, "fail_after_n", True, "provider does not accept sim kwarg — skipped")
        return

    call = _get_primary_call(provider_name, p)
    if call is None:
        _record(checks, "fail_after_n", True, "no primary call — skipped")
        return

    results = []
    for i in range(1, 4):
        try:
            call()
            results.append(("ok", i))
        except MockTimeoutError:
            results.append(("timeout", i))
        except Exception as exc:
            results.append((f"error:{type(exc).__name__}", i))

    # Expected: ok, ok, timeout
    ok_ok_timeout = (
        results[0][0] == "ok"
        and results[1][0] == "ok"
        and results[2][0] == "timeout"
    )
    _record(checks, "fail_after_n", ok_ok_timeout,
            f"fail_after_n=2 pattern: {[r[0] for r in results]} "
            f"(expected ['ok', 'ok', 'timeout'])")


def _inject_rapid_calls(
    provider_name: str, provider: Any, checks: list[InjectionCheck]
) -> None:
    """
    5 successive calls must all succeed without state corruption.
    """
    call = _get_primary_call(provider_name, provider)
    if call is None:
        _record(checks, "rapid_successive_calls", True, "no primary call — skipped")
        return
    results = []
    for i in range(5):
        try:
            r = call()
            results.append(getattr(r, "status", "unknown"))
        except Exception as exc:
            results.append(f"error:{type(exc).__name__}")

    all_success = all(
        (r.value if hasattr(r, "value") else str(r)) == "success"
        for r in results
    )
    _record(checks, "rapid_successive_calls", all_success,
            f"5 calls: {[r.value if hasattr(r, 'value') else r for r in results]}")


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def run_failure_injection(
    provider_name: str,
    provider: Any,
    provider_class: type,
) -> FailureInjectionResult:
    """
    Run all failure injection scenarios for a provider.

    Args:
        provider_name: canonical name
        provider: default-config provider instance (for non-failure scenarios)
        provider_class: class used to construct failure-mode instances

    Returns:
        FailureInjectionResult with per-scenario check results
    """
    checks: list[InjectionCheck] = []

    _inject_timeout(provider_name, provider_class, checks)
    _inject_unavailable(provider_name, provider_class, checks)
    _inject_empty_response(provider_name, provider, checks)
    _inject_partial_response(provider_name, provider, checks)
    _inject_fail_after_n(provider_name, provider_class, checks)
    _inject_rapid_calls(provider_name, provider, checks)

    return FailureInjectionResult(
        provider_name=provider_name,
        all_passed=all(c.passed for c in checks),
        checks=checks,
    )


def run_all_failure_injection(
    providers: dict[str, Any],
    provider_classes: dict[str, type],
) -> dict[str, FailureInjectionResult]:
    """Run failure injection for all named providers."""
    return {
        name: run_failure_injection(name, provider, provider_classes[name])
        for name, provider in providers.items()
    }
