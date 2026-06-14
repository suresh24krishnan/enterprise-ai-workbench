"""
Enterprise Data Warehouse (EDW) provider contracts.

Defines the read interface for historical claims data, customer profiles,
loss trends, and risk scoring sourced from the enterprise data warehouse.

IMPORTANT — Specification alignment (ADR-004):
  EDW query interfaces and response schemas must be derived from the internal
  enterprise EDW API specification. Request this specification from the
  IT Architecture / Data Engineering team before implementing the real adapter.

  EDW-specific notes:
    - EDW data is typically read-only and may be 24–48 hours behind live
      ClaimCenter data. Do not use EDW for real-time claim status.
    - EDW identifiers may differ from ClaimCenter identifiers. The adapter
      must resolve cross-system identifiers at the boundary.
    - Historical claim records from EDW may include claims not visible in
      the adjuster's current ClaimCenter portfolio. Apply portfolio scoping
      at the query level, not after retrieval.

No write interface for EDW — the platform never writes to the data warehouse.

ERROR HANDLING (all implementations):
  - 404: customer or claim history not found → NOT_FOUND
  - 403: adjuster lacks read permission for historical data → PERMISSION_DENIED
  - 429: rate limit / query quota exceeded → RATE_LIMITED (retryable=True)
  - 503: EDW unavailable → UNAVAILABLE (retryable=True)
  - Complex queries may time out — treat as UNAVAILABLE (retryable=True)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

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


# ---------------------------------------------------------------------------
# EDW-specific enums
# ---------------------------------------------------------------------------


class RiskTier(str, Enum):
    """Customer risk tier as computed by the EDW risk scoring model."""

    LOW = "low"
    STANDARD = "standard"
    ELEVATED = "elevated"
    HIGH = "high"
    WATCH = "watch"


class LossTrendDirection(str, Enum):
    """Direction of loss frequency or severity trend over a period."""

    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"
    INSUFFICIENT_DATA = "insufficient_data"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ClaimHistorySummary(BaseModel):
    """
    A historical claim record from the EDW. May include claims from
    prior policy terms and lines of business.

    NOTE: This is a summary view. Full historical claim detail is in
    ClaimCenter; the EDW provides aggregated and historical context only.
    """

    historical_claim_id: str = Field(description="EDW claim identifier")
    claim_number: str | None = None
    policy_number: str | None = None
    line_of_business: ClaimLineOfBusiness | None = None
    status: ClaimStatus | None = None
    loss_date: date | None = None
    closed_date: date | None = None
    total_incurred: MoneyAmount | None = None
    total_paid: MoneyAmount | None = None
    loss_cause: str | None = None
    at_fault: bool | None = Field(
        default=None,
        description="Whether the insured was at fault (auto LOB)",
    )
    litigation_flag: bool = False
    source_system: SourceSystem = SourceSystem.EDW


class CustomerProfile(BaseModel):
    """
    Aggregated customer profile from the EDW, spanning all policies and claims.

    NOTE — Specification alignment:
      The EDW customer entity may use a different identifier than ClaimCenter's
      Contact entity. The adapter must resolve the cross-system customer key.
    """

    customer_id: str = Field(description="EDW customer identifier")
    claimcenter_contact_id: str | None = None
    policy_count: int = Field(default=0, description="Total active policies")
    years_as_customer: int | None = None
    lifetime_claims_count: int = Field(default=0)
    lifetime_claims_paid: MoneyAmount | None = None
    open_claims_count: int = Field(default=0)
    risk_tier: RiskTier = RiskTier.STANDARD
    risk_score: Decimal | None = Field(
        default=None,
        description="Numerical risk score (0–100, higher = more risk)",
    )
    preferred_contact_method: str | None = None
    source_system: SourceSystem = SourceSystem.EDW


class LossTrendSummary(BaseModel):
    """
    Loss trend data for a customer or portfolio segment over a time period.
    Used to contextualise claim frequency and severity.
    """

    period_months: int = Field(description="Number of months the trend covers")
    from_date: date
    to_date: date
    claim_count: int
    total_incurred: MoneyAmount | None = None
    average_incurred: MoneyAmount | None = None
    frequency_trend: LossTrendDirection
    severity_trend: LossTrendDirection
    prior_period_claim_count: int | None = None
    prior_period_total_incurred: MoneyAmount | None = None
    line_of_business: ClaimLineOfBusiness | None = None


class RiskProfile(BaseModel):
    """
    Comprehensive risk profile combining customer history and EDW scoring.
    Used by the AI supervisor to contextualise governance thresholds and
    escalation recommendations.
    """

    customer_id: str
    risk_tier: RiskTier
    risk_score: Decimal | None = None
    fraud_risk_score: Decimal | None = Field(
        default=None,
        description="Fraud propensity score (0–100, higher = more risk)",
    )
    prior_fraud_flags: int = Field(default=0)
    prior_siu_referrals: int = Field(default=0)
    litigation_history: bool = False
    large_loss_history: bool = Field(
        default=False,
        description="True if customer has prior claims exceeding a large-loss threshold",
    )
    loss_trend: LossTrendSummary | None = None
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Human-readable risk factor descriptions for adjuster context",
    )
    data_as_of: date | None = None
    source_system: SourceSystem = SourceSystem.EDW


# ---------------------------------------------------------------------------
# Provider result wrappers
# ---------------------------------------------------------------------------


class GetClaimHistoryResult(BaseModel):
    status: ToolResultStatus
    claims: list[ClaimHistorySummary] = Field(default_factory=list)
    total_count: int = 0
    error: ToolError | None = None


class GetCustomerProfileResult(BaseModel):
    status: ToolResultStatus
    profile: CustomerProfile | None = None
    error: ToolError | None = None


class GetLossTrendsResult(BaseModel):
    status: ToolResultStatus
    trend: LossTrendSummary | None = None
    error: ToolError | None = None


class GetRiskProfileResult(BaseModel):
    status: ToolResultStatus
    risk_profile: RiskProfile | None = None
    error: ToolError | None = None


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class IEDWReadProvider(Protocol):
    """
    Read interface for the Enterprise Data Warehouse.

    All implementations — mock, hybrid, real — must satisfy this protocol.

    SPECIFICATION ALIGNMENT (ADR-004):
      The real adapter must be derived from the internal EDW API specification.
      Request the specification from IT Architecture / Data Engineering before
      implementation. EDW APIs may be REST, JDBC, or proprietary — confirm
      the interface type before building the adapter.
    """

    def health(self) -> ProviderStatus:
        """Report provider operational status."""
        ...

    def get_claim_history(
        self,
        customer_id: str,
        context: ToolExecutionContext,
        line_of_business: ClaimLineOfBusiness | None = None,
        years_back: int = 5,
    ) -> GetClaimHistoryResult:
        """
        Retrieve historical claims for a customer from the EDW.
        Optionally filtered by line of business and time window.
        """
        ...

    def get_customer_profile(
        self,
        customer_id: str,
        context: ToolExecutionContext,
    ) -> GetCustomerProfileResult:
        """Retrieve aggregated customer profile from the EDW."""
        ...

    def get_loss_trends(
        self,
        customer_id: str,
        context: ToolExecutionContext,
        period_months: int = 36,
        line_of_business: ClaimLineOfBusiness | None = None,
    ) -> GetLossTrendsResult:
        """
        Retrieve loss frequency and severity trends for a customer.
        Compared to prior period of the same length.
        """
        ...

    def get_risk_profile(
        self,
        customer_id: str,
        context: ToolExecutionContext,
    ) -> GetRiskProfileResult:
        """
        Retrieve the comprehensive risk profile for a customer.
        Includes risk tier, fraud score, SIU history, and loss trends.
        """
        ...
