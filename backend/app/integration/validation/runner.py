"""
Validation runner — orchestrates the full adapter validation suite.

Loads all registered providers from the registry, runs all four validation
dimensions, and returns a structured report per provider.

Report format (per provider):
  {
    "provider": "claimcenter",
    "contract_compliance": true,
    "schema_valid": true,
    "error_handling_valid": true,
    "failure_modes_supported": true,
    "overall_status": "PASS"   # or "FAIL"
  }

Modes:
  DRY_RUN  — checks registry wiring and contract structure only.
             Does not call any provider methods. No data access.
  FULL     — runs all four dimensions including response and failure tests.
             Calls mock provider methods against fixture data.

Safety:
  - MOCK mode only — validation never activates real providers
  - All provider resolutions use the configured registry
  - Exceptions from individual providers are caught and recorded;
    one broken provider does not abort the suite

Usage:
  from backend.app.integration.validation.runner import run_validation, RunMode
  report = run_validation(mode=RunMode.FULL)
  for entry in report.provider_results:
      print(entry.provider, entry.overall_status)
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from backend.app.integration.bootstrap import _build_registry
from backend.app.integration.mocks.claimcenter import MockClaimCenterProvider
from backend.app.integration.mocks.documents import MockDocumentProvider
from backend.app.integration.mocks.edw import MockEDWProvider
from backend.app.integration.mocks.email import MockEmailProvider
from backend.app.integration.mocks.fraud import MockFraudProvider
from backend.app.integration.mocks.policycenter import MockPolicyCenterProvider
from backend.app.integration.providers import ProviderName
from backend.app.integration.registry import ProviderRegistry
from backend.app.integration.validation.contract_validator import validate_all_contracts
from backend.app.integration.validation.error_validator import validate_all_error_handling
from backend.app.integration.validation.failure_injection import run_all_failure_injection
from backend.app.integration.validation.response_validator import validate_all_responses


class RunMode(str, Enum):
    DRY_RUN = "dry_run"
    FULL = "full"


# Provider class registry — used to construct failure-mode instances
_PROVIDER_CLASSES: dict[str, type] = {
    ProviderName.CLAIMCENTER:  MockClaimCenterProvider,
    ProviderName.POLICYCENTER: MockPolicyCenterProvider,
    ProviderName.EDW:          MockEDWProvider,
    ProviderName.DOCUMENTS:    MockDocumentProvider,
    ProviderName.FRAUD:        MockFraudProvider,
    ProviderName.EMAIL:        MockEmailProvider,
}


@dataclass
class ProviderValidationResult:
    provider: str
    contract_compliance: bool
    schema_valid: bool
    error_handling_valid: bool
    failure_modes_supported: bool
    overall_status: str  # "PASS" | "FAIL" | "DRY_RUN_PASS"
    contract_summary: str = ""
    schema_summary: str = ""
    error_summary: str = ""
    failure_summary: str = ""
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "contract_compliance": self.contract_compliance,
            "schema_valid": self.schema_valid,
            "error_handling_valid": self.error_handling_valid,
            "failure_modes_supported": self.failure_modes_supported,
            "overall_status": self.overall_status,
            "contract_summary": self.contract_summary,
            "schema_summary": self.schema_summary,
            "error_summary": self.error_summary,
            "failure_summary": self.failure_summary,
            "violations": self.violations,
        }


@dataclass
class ValidationReport:
    run_mode: str
    run_at: str
    provider_results: list[ProviderValidationResult] = field(default_factory=list)
    total_providers: int = 0
    passed: int = 0
    failed: int = 0
    overall_status: str = "PASS"

    def to_dict(self) -> dict:
        return {
            "run_mode": self.run_mode,
            "run_at": self.run_at,
            "total_providers": self.total_providers,
            "passed": self.passed,
            "failed": self.failed,
            "overall_status": self.overall_status,
            "providers": [r.to_dict() for r in self.provider_results],
        }

    @property
    def validation_summary(self) -> dict:
        """Safe subset for the /api/integration/status endpoint."""
        return {
            "run_mode": self.run_mode,
            "run_at": self.run_at,
            "total_providers": self.total_providers,
            "passed": self.passed,
            "failed": self.failed,
            "overall_status": self.overall_status,
        }


def _collect_providers(registry: ProviderRegistry) -> dict[str, Any]:
    """Resolve all registered providers from the registry."""
    return {name: registry.resolve(name) for name in ProviderName.ALL}


def run_validation(
    mode: RunMode = RunMode.FULL,
    registry: ProviderRegistry | None = None,
) -> ValidationReport:
    """
    Run the adapter validation suite.

    Args:
        mode: DRY_RUN (contract + wiring checks only) or FULL (all dimensions)
        registry: optional registry override; uses _build_registry() if None

    Returns:
        ValidationReport with structured results per provider
    """
    run_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    reg = registry or _build_registry()
    providers = _collect_providers(reg)
    provider_names = list(providers.keys())

    # --- Contract validation (always runs — structural, no method calls) ---
    contract_results = validate_all_contracts(providers)

    if mode == RunMode.DRY_RUN:
        results = []
        for name in provider_names:
            cr = contract_results[name]
            status = "DRY_RUN_PASS" if cr.compliant else "FAIL"
            violations = [f"[contract] {v.detail}" for v in cr.violations]
            results.append(ProviderValidationResult(
                provider=name,
                contract_compliance=cr.compliant,
                schema_valid=True,   # not tested in dry run
                error_handling_valid=True,
                failure_modes_supported=True,
                overall_status=status,
                contract_summary=cr.summary,
                schema_summary="skipped (dry run)",
                error_summary="skipped (dry run)",
                failure_summary="skipped (dry run)",
                violations=violations,
            ))

        passed = sum(1 for r in results if "PASS" in r.overall_status)
        failed = sum(1 for r in results if r.overall_status == "FAIL")
        return ValidationReport(
            run_mode=mode.value,
            run_at=run_at,
            provider_results=results,
            total_providers=len(results),
            passed=passed,
            failed=failed,
            overall_status="PASS" if failed == 0 else "FAIL",
        )

    # --- Full suite ---
    response_results = validate_all_responses(providers)
    error_results = validate_all_error_handling(providers, _PROVIDER_CLASSES)
    injection_results = run_all_failure_injection(providers, _PROVIDER_CLASSES)

    results = []
    for name in provider_names:
        cr = contract_results[name]
        rr = response_results[name]
        er = error_results[name]
        ir = injection_results[name]

        overall_pass = cr.compliant and rr.valid and er.valid and ir.all_passed
        status = "PASS" if overall_pass else "FAIL"

        all_violations = (
            [f"[contract] {v.detail}" for v in cr.violations]
            + [f"[schema] {v.detail}" for v in rr.violations]
            + [f"[error] {v.detail}" for v in er.violations]
            + [f"[injection] {c.name}: {c.detail}" for c in ir.checks if not c.passed]
        )

        results.append(ProviderValidationResult(
            provider=name,
            contract_compliance=cr.compliant,
            schema_valid=rr.valid,
            error_handling_valid=er.valid,
            failure_modes_supported=ir.all_passed,
            overall_status=status,
            contract_summary=cr.summary,
            schema_summary=rr.summary,
            error_summary=er.summary,
            failure_summary=ir.summary,
            violations=all_violations,
        ))

    passed = sum(1 for r in results if r.overall_status == "PASS")
    failed = sum(1 for r in results if r.overall_status == "FAIL")
    return ValidationReport(
        run_mode=mode.value,
        run_at=run_at,
        provider_results=results,
        total_providers=len(results),
        passed=passed,
        failed=failed,
        overall_status="PASS" if failed == 0 else "FAIL",
    )
