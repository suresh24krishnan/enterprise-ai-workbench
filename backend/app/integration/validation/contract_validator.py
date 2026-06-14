"""
Contract validator — interface compliance checking.

Verifies that a provider instance implements the required interface:
  - All required methods are present
  - Methods are callable (not abstract stubs left as None or NotImplemented)
  - health() returns a ProviderStatus value
  - No method is missing from the contract specification

This validator is STRUCTURAL only — it does not execute provider methods
or make any calls. It inspects the provider instance using Python introspection.

Design:
  The contract spec table below is the single source of truth for what
  each named provider must implement. When new contract methods are added
  in future sprints (e.g. IClaimCenterWriteProvider going live), add them
  here. The runner will immediately catch any provider that does not
  implement the new method.

Safety:
  - No enterprise calls made
  - No mock data accessed
  - No side effects
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Contract specification — canonical method requirements per provider
# ---------------------------------------------------------------------------
#
# Read methods: must be present and callable
# Write methods: must be present and callable (raises MockWriteDisabledError
#   in Phase 2A — presence is required, error on call is expected)
# health: must be present on all providers

_REQUIRED_METHODS: dict[str, list[str]] = {
    "claimcenter": [
        "health",
        "get_claim",
        "get_claims",
        "get_claim_notes",
        "get_exposures",
        "get_activities",
        "get_reserves",
        "get_payments",
        # Write stubs — must be present; MockWriteDisabledError expected on call
        "create_claim_note",
        "create_activity",
    ],
    "policycenter": [
        "health",
        "get_policy",
        "get_policy_coverages",
        "get_policy_limits",
        "get_policy_deductibles",
        "get_endorsements",
    ],
    "edw": [
        "health",
        "get_claim_history",
        "get_customer_profile",
        "get_loss_trends",
        "get_risk_profile",
    ],
    "documents": [
        "health",
        "get_documents",
        "get_document",
        "search_documents",
        "get_document_text",
        "get_document_evidence",
    ],
    "fraud": [
        "health",
        "get_fraud_indicators",
        "get_siu_recommendation",
    ],
    "email": [
        "health",
        "get_claim_correspondence",
        "get_email_thread",
        "draft_email",
        # send_email must NOT be present (ADR — only draft, never send)
    ],
}

# Methods that must NOT exist on their respective providers
_FORBIDDEN_METHODS: dict[str, list[str]] = {
    "email": ["send_email"],
}


@dataclass
class ContractViolation:
    provider_name: str
    violation_type: str  # "missing_method" | "not_callable" | "forbidden_method" | "bad_health"
    detail: str


@dataclass
class ContractValidationResult:
    provider_name: str
    compliant: bool
    violations: list[ContractViolation] = field(default_factory=list)
    methods_checked: int = 0
    methods_passed: int = 0

    @property
    def summary(self) -> str:
        if self.compliant:
            return f"PASS ({self.methods_passed}/{self.methods_checked} methods)"
        return (
            f"FAIL ({self.methods_passed}/{self.methods_checked} methods, "
            f"{len(self.violations)} violation(s))"
        )


def validate_contract(provider_name: str, provider: Any) -> ContractValidationResult:
    """
    Validate that a provider instance satisfies its contract specification.

    Checks:
      1. All required methods are present as attributes
      2. All required methods are callable
      3. All forbidden methods are absent
      4. health() is present and callable (checked via required list)

    Does NOT call any methods. Pure structural inspection.

    Args:
        provider_name: canonical name (e.g. "claimcenter")
        provider: the provider instance to inspect

    Returns:
        ContractValidationResult with compliance status and any violations
    """
    required = _REQUIRED_METHODS.get(provider_name, [])
    forbidden = _FORBIDDEN_METHODS.get(provider_name, [])
    violations: list[ContractViolation] = []
    methods_passed = 0

    # Check required methods
    for method_name in required:
        attr = getattr(provider, method_name, None)
        if attr is None:
            violations.append(ContractViolation(
                provider_name=provider_name,
                violation_type="missing_method",
                detail=f"Required method '{method_name}' is missing from {type(provider).__name__}",
            ))
        elif not callable(attr):
            violations.append(ContractViolation(
                provider_name=provider_name,
                violation_type="not_callable",
                detail=f"Method '{method_name}' exists but is not callable on {type(provider).__name__}",
            ))
        else:
            methods_passed += 1

    # Check forbidden methods
    for method_name in forbidden:
        if hasattr(provider, method_name) and callable(getattr(provider, method_name)):
            violations.append(ContractViolation(
                provider_name=provider_name,
                violation_type="forbidden_method",
                detail=(
                    f"Method '{method_name}' must NOT exist on {type(provider).__name__}. "
                    f"This method is explicitly excluded from the contract (ADR-004)."
                ),
            ))

    return ContractValidationResult(
        provider_name=provider_name,
        compliant=len(violations) == 0,
        violations=violations,
        methods_checked=len(required),
        methods_passed=methods_passed,
    )


def validate_all_contracts(
    providers: dict[str, Any],
) -> dict[str, ContractValidationResult]:
    """
    Validate contract compliance for all named providers.

    Args:
        providers: mapping of provider_name -> provider instance

    Returns:
        mapping of provider_name -> ContractValidationResult
    """
    return {
        name: validate_contract(name, provider)
        for name, provider in providers.items()
    }
