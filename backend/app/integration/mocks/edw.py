"""
Mock Enterprise Data Warehouse (EDW) provider — specification-shaped simulation.

Implements IEDWReadProvider using realistic analytics data for ABC Logistics
(customer of 6 years, standard risk tier, prior commercial auto losses).

IMPORTANT — Specification alignment (ADR-004):
  The real EDW adapter must be derived from the internal enterprise EDW API
  specification. EDW APIs may be REST, JDBC, OData, or proprietary — confirm
  the interface type before building. Key mappings to confirm from the spec:
    Customer entity key in EDW vs. ClaimCenter Contact publicID
    Loss amount field types (decimal vs. string vs. currency object)
    Date formats (ISO 8601 vs. EDW-specific)
    Risk score scale (confirm 0–100 or different range)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.app.integration.contracts.common import (
    ClaimLineOfBusiness,
    ClaimStatus,
    MoneyAmount,
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)
from backend.app.integration.contracts.edw import (
    ClaimHistorySummary,
    CustomerProfile,
    GetClaimHistoryResult,
    GetCustomerProfileResult,
    GetLossTrendsResult,
    GetRiskProfileResult,
    IEDWReadProvider,
    LossTrendDirection,
    LossTrendSummary,
    RiskProfile,
    RiskTier,
)
from backend.app.integration.mocks.simulation import SimulationConfig, apply_simulation

_CUSTOMER_ID = "EDW-CUST-10042"
_CC_CONTACT_ID = "CC-CONTACT-10042"

_CUSTOMER_PROFILE = CustomerProfile(
    customer_id=_CUSTOMER_ID,
    claimcenter_contact_id=_CC_CONTACT_ID,
    policy_count=2,
    years_as_customer=6,
    lifetime_claims_count=4,
    lifetime_claims_paid=MoneyAmount(amount=Decimal("28400.00"), currency="USD"),
    open_claims_count=1,
    risk_tier=RiskTier.STANDARD,
    risk_score=Decimal("38.0"),
    preferred_contact_method="email",
    source_system=SourceSystem.EDW,
)

_CLAIM_HISTORY = [
    ClaimHistorySummary(
        historical_claim_id="EDW-CLM-2023-001",
        claim_number="CLM-2023-044201",
        policy_number="CA-2021-4412",
        line_of_business=ClaimLineOfBusiness.COMMERCIAL,
        status=ClaimStatus.CLOSED,
        loss_date=date(2023, 3, 14),
        closed_date=date(2023, 5, 20),
        total_incurred=MoneyAmount(amount=Decimal("11200.00"), currency="USD"),
        total_paid=MoneyAmount(amount=Decimal("11200.00"), currency="USD"),
        loss_cause="Vehicle collision — insured at fault",
        at_fault=True,
        litigation_flag=False,
        source_system=SourceSystem.EDW,
    ),
    ClaimHistorySummary(
        historical_claim_id="EDW-CLM-2022-001",
        claim_number="CLM-2022-031804",
        policy_number="CA-2021-4412",
        line_of_business=ClaimLineOfBusiness.COMMERCIAL,
        status=ClaimStatus.CLOSED,
        loss_date=date(2022, 8, 5),
        closed_date=date(2022, 9, 30),
        total_incurred=MoneyAmount(amount=Decimal("9800.00"), currency="USD"),
        total_paid=MoneyAmount(amount=Decimal("9800.00"), currency="USD"),
        loss_cause="Theft — cargo theft from unattended vehicle",
        at_fault=None,
        litigation_flag=False,
        source_system=SourceSystem.EDW,
    ),
    ClaimHistorySummary(
        historical_claim_id="EDW-CLM-2021-001",
        claim_number="CLM-2021-018822",
        policy_number="CA-2019-2201",
        line_of_business=ClaimLineOfBusiness.COMMERCIAL,
        status=ClaimStatus.CLOSED,
        loss_date=date(2021, 1, 19),
        closed_date=date(2021, 4, 12),
        total_incurred=MoneyAmount(amount=Decimal("7400.00"), currency="USD"),
        total_paid=MoneyAmount(amount=Decimal("7400.00"), currency="USD"),
        loss_cause="Rear-end collision — third party at fault",
        at_fault=False,
        litigation_flag=False,
        source_system=SourceSystem.EDW,
    ),
]

_LOSS_TREND = LossTrendSummary(
    period_months=36,
    from_date=date(2023, 6, 1),
    to_date=date(2026, 6, 1),
    claim_count=2,
    total_incurred=MoneyAmount(amount=Decimal("19600.00"), currency="USD"),
    average_incurred=MoneyAmount(amount=Decimal("9800.00"), currency="USD"),
    frequency_trend=LossTrendDirection.STABLE,
    severity_trend=LossTrendDirection.IMPROVING,
    prior_period_claim_count=2,
    prior_period_total_incurred=MoneyAmount(amount=Decimal("21000.00"), currency="USD"),
    line_of_business=ClaimLineOfBusiness.COMMERCIAL,
)

_RISK_PROFILE = RiskProfile(
    customer_id=_CUSTOMER_ID,
    risk_tier=RiskTier.STANDARD,
    risk_score=Decimal("38.0"),
    fraud_risk_score=Decimal("12.0"),
    prior_fraud_flags=0,
    prior_siu_referrals=0,
    litigation_history=False,
    large_loss_history=False,
    loss_trend=_LOSS_TREND,
    risk_factors=[
        "Fleet operator — higher base frequency expected for commercial auto",
        "4 prior claims over 6 years — within expected range for fleet size",
        "No fraud flags or SIU referrals in claim history",
        "Severity trend improving over trailing 36 months",
    ],
    data_as_of=date(2026, 6, 12),
    source_system=SourceSystem.EDW,
)


class MockEDWProvider:
    """
    Specification-shaped mock for EDW read access.

    Returns analytics for customer EDW-CUST-10042 (ABC Logistics).
    Returns NOT_FOUND for all other customer IDs.

    NOTE — Specification alignment (ADR-004):
      The real EDW adapter must be derived from the internal EDW API spec.
      Request the spec from IT Architecture / Data Engineering before building.
    """

    def __init__(self, sim: SimulationConfig | None = None) -> None:
        self._sim = sim or SimulationConfig()

    def health(self) -> ProviderStatus:
        return ProviderStatus.MOCK

    def _not_found(self, customer_id: str) -> ToolError:
        return ToolError(
            code="NOT_FOUND",
            message=f"Customer '{customer_id}' not found in EDW.",
            source_system=SourceSystem.EDW,
            retryable=False,
        )

    def get_claim_history(
        self,
        customer_id: str,
        context: ToolExecutionContext,
        line_of_business: ClaimLineOfBusiness | None = None,
        years_back: int = 5,
    ) -> GetClaimHistoryResult:
        apply_simulation(self._sim)
        if customer_id != _CUSTOMER_ID:
            return GetClaimHistoryResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(customer_id))
        history = _CLAIM_HISTORY
        if line_of_business:
            history = [c for c in history if c.line_of_business == line_of_business]
        return GetClaimHistoryResult(
            status=ToolResultStatus.SUCCESS, claims=history, total_count=len(history)
        )

    def get_customer_profile(
        self, customer_id: str, context: ToolExecutionContext
    ) -> GetCustomerProfileResult:
        apply_simulation(self._sim)
        if customer_id != _CUSTOMER_ID:
            return GetCustomerProfileResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(customer_id))
        return GetCustomerProfileResult(status=ToolResultStatus.SUCCESS, profile=_CUSTOMER_PROFILE)

    def get_loss_trends(
        self,
        customer_id: str,
        context: ToolExecutionContext,
        period_months: int = 36,
        line_of_business: ClaimLineOfBusiness | None = None,
    ) -> GetLossTrendsResult:
        apply_simulation(self._sim)
        if customer_id != _CUSTOMER_ID:
            return GetLossTrendsResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(customer_id))
        return GetLossTrendsResult(status=ToolResultStatus.SUCCESS, trend=_LOSS_TREND)

    def get_risk_profile(
        self, customer_id: str, context: ToolExecutionContext
    ) -> GetRiskProfileResult:
        apply_simulation(self._sim)
        if customer_id != _CUSTOMER_ID:
            return GetRiskProfileResult(status=ToolResultStatus.NOT_FOUND, error=self._not_found(customer_id))
        return GetRiskProfileResult(status=ToolResultStatus.SUCCESS, risk_profile=_RISK_PROFILE)
