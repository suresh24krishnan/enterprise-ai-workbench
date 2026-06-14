"""
Mock PolicyCenter provider — specification-shaped simulation.

Implements IPolicyCenterReadProvider using a realistic Commercial Auto
policy context consistent with the Phase 1 claim scenario (CLM-2026-100245,
ABC Logistics, policy CA-2024-8812).

IMPORTANT — Specification alignment (ADR-004):
  When the real PolicyCenter adapter is built, field names must be mapped
  from the Guidewire PolicyCenter REST API specification. Key mappings
  to confirm:
    PolicyPeriod.policyNumber   → policy_number
    PolicyPeriod.effectiveDate  → effective_date
    PolicyPeriod.expirationDate → expiration_date
    PolicyLine.coverages[]      → CoverageSummary[]
    Coverage.covTerms[]         → LimitSummary[] / DeductibleSummary[]
    CovTerm.amount.amount       → MoneyAmount.amount (Decimal)

No write interface — PolicyCenter is read-only for the claims platform.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.app.integration.contracts.common import (
    ClaimLineOfBusiness,
    MoneyAmount,
    PartySummary,
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)
from backend.app.integration.contracts.policycenter import (
    CoverageSummary,
    CoverageStatus,
    DeductibleSummary,
    DeductibleType,
    EndorsementSummary,
    GetEndorsementsResult,
    GetPolicyCoveragesResult,
    GetPolicyDeductiblesResult,
    GetPolicyLimitsResult,
    GetPolicyResult,
    IPolicyCenterReadProvider,
    LimitSummary,
    LimitType,
    PolicyStatus,
    PolicySummary,
)
from backend.app.integration.mocks.simulation import SimulationConfig, apply_simulation

_POLICY_ID = "POL-CA-2024-8812"
_POLICY_NUMBER = "CA-2024-8812"

_INSURED = PartySummary(
    party_id="pty-001",
    source_system=SourceSystem.POLICYCENTER,
    source_id="PC-ACCOUNT-4421",
    display_name="ABC Logistics Inc.",
    role="named_insured",
    email="insurance@abclogistics.local",
    phone="305-555-0192",
)

_POLICY = PolicySummary(
    policy_id=_POLICY_ID,
    policy_number=_POLICY_NUMBER,
    line_of_business=ClaimLineOfBusiness.COMMERCIAL,
    status=PolicyStatus.IN_FORCE,
    effective_date=date(2024, 1, 1),
    expiration_date=date(2027, 1, 1),
    insured=_INSURED,
    carrier="Enterprise Mutual Insurance Co.",
    program="Commercial Fleet Auto",
    source_system=SourceSystem.POLICYCENTER,
)

_COVERAGES = [
    CoverageSummary(
        coverage_id="cov-001",
        policy_id=_POLICY_ID,
        coverage_type="BI",
        coverage_description="Bodily Injury Liability",
        status=CoverageStatus.ACTIVE,
        effective_date=date(2024, 1, 1),
        expiration_date=date(2027, 1, 1),
        per_occurrence_limit=MoneyAmount(amount=Decimal("1000000.00"), currency="USD"),
        deductible=MoneyAmount(amount=Decimal("5000.00"), currency="USD"),
        applies_to_claim_line="auto_liability",
    ),
    CoverageSummary(
        coverage_id="cov-002",
        policy_id=_POLICY_ID,
        coverage_type="COLL",
        coverage_description="Physical Damage — Collision",
        status=CoverageStatus.ACTIVE,
        effective_date=date(2024, 1, 1),
        expiration_date=date(2027, 1, 1),
        per_occurrence_limit=MoneyAmount(amount=Decimal("250000.00"), currency="USD"),
        deductible=MoneyAmount(amount=Decimal("2500.00"), currency="USD"),
        applies_to_claim_line="physical_damage",
    ),
    CoverageSummary(
        coverage_id="cov-003",
        policy_id=_POLICY_ID,
        coverage_type="RENT",
        coverage_description="Rental Reimbursement",
        status=CoverageStatus.ACTIVE,
        effective_date=date(2024, 1, 1),
        expiration_date=date(2027, 1, 1),
        per_occurrence_limit=MoneyAmount(amount=Decimal("2250.00"), currency="USD"),
        deductible=MoneyAmount(amount=Decimal("0.00"), currency="USD"),
        applies_to_claim_line="rental",
    ),
]

_LIMITS = [
    LimitSummary(
        limit_id="lim-001",
        coverage_id="cov-001",
        policy_id=_POLICY_ID,
        limit_type=LimitType.PER_OCCURRENCE,
        amount=MoneyAmount(amount=Decimal("1000000.00"), currency="USD"),
        description="Bodily Injury — per occurrence limit",
    ),
    LimitSummary(
        limit_id="lim-002",
        coverage_id="cov-002",
        policy_id=_POLICY_ID,
        limit_type=LimitType.PER_OCCURRENCE,
        amount=MoneyAmount(amount=Decimal("250000.00"), currency="USD"),
        description="Physical Damage — Collision limit",
    ),
    LimitSummary(
        limit_id="lim-003",
        coverage_id="cov-003",
        policy_id=_POLICY_ID,
        limit_type=LimitType.AGGREGATE,
        amount=MoneyAmount(amount=Decimal("2250.00"), currency="USD"),
        description="Rental Reimbursement — $75/day × 30 days",
    ),
]

_DEDUCTIBLES = [
    DeductibleSummary(
        deductible_id="ded-001",
        coverage_id="cov-001",
        policy_id=_POLICY_ID,
        deductible_type=DeductibleType.FLAT,
        amount=MoneyAmount(amount=Decimal("5000.00"), currency="USD"),
        description="Bodily Injury Liability deductible",
    ),
    DeductibleSummary(
        deductible_id="ded-002",
        coverage_id="cov-002",
        policy_id=_POLICY_ID,
        deductible_type=DeductibleType.FLAT,
        amount=MoneyAmount(amount=Decimal("2500.00"), currency="USD"),
        description="Physical Damage — Collision deductible",
    ),
]

_ENDORSEMENTS = [
    EndorsementSummary(
        endorsement_id="end-001",
        policy_id=_POLICY_ID,
        endorsement_number="END-2024-001",
        description="Scheduled Autos — Fleet Schedule of 14 commercial vehicles",
        effective_date=date(2024, 1, 1),
        premium_impact=MoneyAmount(amount=Decimal("0.00"), currency="USD"),
    ),
    EndorsementSummary(
        endorsement_id="end-002",
        policy_id=_POLICY_ID,
        endorsement_number="END-2024-002",
        description="Hired and Non-Owned Auto Liability Extension",
        effective_date=date(2024, 1, 1),
        premium_impact=MoneyAmount(amount=Decimal("450.00"), currency="USD"),
    ),
]


class MockPolicyCenterProvider:
    """
    Specification-shaped mock for PolicyCenter read access.

    Returns policy CA-2024-8812 for policy ID POL-CA-2024-8812 or
    policy number CA-2024-8812. Returns NOT_FOUND for all other IDs.

    NOTE — Specification alignment (ADR-004):
      The real adapter must map from Guidewire PolicyCenter REST API field
      names to these models. See module docstring for key mappings.
    """

    def __init__(self, sim: SimulationConfig | None = None) -> None:
        self._sim = sim or SimulationConfig()

    def health(self) -> ProviderStatus:
        return ProviderStatus.MOCK

    def _resolve_policy(self, policy_id: str) -> bool:
        return policy_id in (_POLICY_ID, _POLICY_NUMBER)

    def _not_found(self, policy_id: str) -> ToolError:
        return ToolError(
            code="NOT_FOUND",
            message=f"Policy '{policy_id}' not found.",
            source_system=SourceSystem.POLICYCENTER,
            retryable=False,
        )

    def get_policy(self, policy_id: str, context: ToolExecutionContext) -> GetPolicyResult:
        apply_simulation(self._sim)
        if not self._resolve_policy(policy_id):
            return GetPolicyResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(policy_id))
        return GetPolicyResult(status=ToolResultStatus.SUCCESS, policy=_POLICY)

    def get_policy_coverages(
        self,
        policy_id: str,
        context: ToolExecutionContext,
        line_of_business: ClaimLineOfBusiness | None = None,
    ) -> GetPolicyCoveragesResult:
        apply_simulation(self._sim)
        if not self._resolve_policy(policy_id):
            return GetPolicyCoveragesResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(policy_id))
        return GetPolicyCoveragesResult(status=ToolResultStatus.SUCCESS, coverages=_COVERAGES)

    def get_policy_limits(
        self,
        policy_id: str,
        coverage_id: str | None,
        context: ToolExecutionContext,
    ) -> GetPolicyLimitsResult:
        apply_simulation(self._sim)
        if not self._resolve_policy(policy_id):
            return GetPolicyLimitsResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(policy_id))
        limits = _LIMITS if not coverage_id else [l for l in _LIMITS if l.coverage_id == coverage_id]
        return GetPolicyLimitsResult(status=ToolResultStatus.SUCCESS, limits=limits)

    def get_policy_deductibles(
        self,
        policy_id: str,
        coverage_id: str | None,
        context: ToolExecutionContext,
    ) -> GetPolicyDeductiblesResult:
        apply_simulation(self._sim)
        if not self._resolve_policy(policy_id):
            return GetPolicyDeductiblesResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(policy_id))
        deds = _DEDUCTIBLES if not coverage_id else [d for d in _DEDUCTIBLES if d.coverage_id == coverage_id]
        return GetPolicyDeductiblesResult(status=ToolResultStatus.SUCCESS, deductibles=deds)

    def get_endorsements(
        self, policy_id: str, context: ToolExecutionContext
    ) -> GetEndorsementsResult:
        apply_simulation(self._sim)
        if not self._resolve_policy(policy_id):
            return GetEndorsementsResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(policy_id))
        return GetEndorsementsResult(status=ToolResultStatus.SUCCESS, endorsements=_ENDORSEMENTS)
