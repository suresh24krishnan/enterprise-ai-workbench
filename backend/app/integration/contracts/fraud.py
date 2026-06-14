"""
Fraud detection provider contracts.

Defines the read interface for fraud indicators and SIU (Special Investigation
Unit) recommendations sourced from the enterprise fraud detection system.

IMPORTANT — Specification alignment (ADR-004):
  The fraud detection system may be an internal scoring engine, a third-party
  SaaS platform (e.g. FRISS, Shift Technology), or an EDW-based model.
  Obtain the API specification from the SIU / Analytics team before
  implementing the real adapter.

  Fraud system notes:
    - Fraud scores and indicators are advisory — they inform the governance
      engine's ESCALATE threshold, not the final adjuster decision.
    - SIU referral recommendations must be reviewed by a senior adjuster
      before any SIU investigation is initiated. The platform does not
      initiate SIU investigations autonomously.
    - Fraud indicator data is particularly sensitive — access must be
      scoped to the adjuster's claim portfolio and logged in the audit trail.

No write interface — the platform reads fraud indicators but does not
write fraud flags or SIU referrals. Those actions are performed in
ClaimCenter by senior adjusters.

ERROR HANDLING (all implementations):
  - 404: no fraud assessment available for this claim → NOT_FOUND
  - 403: adjuster lacks SIU read access → PERMISSION_DENIED
  - 429: rate limit exceeded → RATE_LIMITED (retryable=True)
  - 503: fraud system unavailable → UNAVAILABLE (retryable=True)
  - Fraud scores may be unavailable for new claims (insufficient history)
    → return NOT_FOUND with a descriptive error, not an empty assessment
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from backend.app.integration.contracts.common import (
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)


# ---------------------------------------------------------------------------
# Fraud-specific enums
# ---------------------------------------------------------------------------


class FraudIndicatorType(str, Enum):
    """Category of fraud indicator signal."""

    PRIOR_CLAIM_PATTERN = "prior_claim_pattern"
    LATE_REPORTING = "late_reporting"
    INCONSISTENT_STATEMENT = "inconsistent_statement"
    SUSPICIOUS_TIMING = "suspicious_timing"
    KNOWN_FRAUD_NETWORK = "known_fraud_network"
    STAGED_ACCIDENT_PATTERN = "staged_accident_pattern"
    MEDICAL_MILL_PROVIDER = "medical_mill_provider"
    INFLATED_DAMAGE = "inflated_damage"
    IDENTITY_MISMATCH = "identity_mismatch"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    ATTORNEY_INVOLVEMENT = "attorney_involvement"
    OTHER = "other"


class FraudRiskLevel(str, Enum):
    """Overall fraud risk classification for a claim."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    INSUFFICIENT_DATA = "insufficient_data"


class SIURecommendationStatus(str, Enum):
    """SIU referral recommendation from the fraud system."""

    NO_REFERRAL = "no_referral"
    MONITOR = "monitor"
    REFER = "refer"
    URGENT_REFER = "urgent_refer"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class FraudIndicator(BaseModel):
    """
    A single fraud signal detected on a claim by the fraud detection system.

    NOTE: Fraud indicators are advisory signals, not fraud determinations.
    The adjuster and governance engine use these as input — they do not
    constitute a finding of fraud. All fraud determinations require human review.
    """

    indicator_id: str
    claim_id: str
    indicator_type: FraudIndicatorType
    description: str = Field(
        description="Human-readable description of the fraud signal"
    )
    confidence: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Confidence score for this indicator (0.0–1.0)",
    )
    detected_at: datetime
    source_system: SourceSystem = SourceSystem.FRAUD
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="References to supporting data points (document IDs, event codes)",
    )


class FraudAssessment(BaseModel):
    """
    Overall fraud risk assessment for a claim, aggregating all indicators.

    The fraud assessment is produced by the enterprise fraud system and
    reflects all available signals at the time of assessment. It should
    be re-requested if significant new claim information is added.
    """

    assessment_id: str
    claim_id: str
    risk_level: FraudRiskLevel
    fraud_score: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("100"),
        description="Composite fraud score (0–100, higher = more risk)",
    )
    indicators: list[FraudIndicator] = Field(default_factory=list)
    assessed_at: datetime
    model_version: str | None = Field(
        default=None,
        description="Version of the fraud model that produced this assessment",
    )
    siu_recommendation: SIURecommendationStatus = SIURecommendationStatus.NO_REFERRAL
    prior_fraud_flags_on_customer: int = Field(
        default=0,
        description="Count of prior fraud flags on this customer across all claims",
    )
    source_system: SourceSystem = SourceSystem.FRAUD


class SIURecommendation(BaseModel):
    """
    SIU referral recommendation with supporting rationale.

    IMPORTANT: This recommendation is advisory. A senior adjuster must
    review and approve any SIU referral before it is initiated. The
    platform does not initiate SIU investigations autonomously.
    The governance engine will ESCALATE claims with REFER or URGENT_REFER
    recommendations — human review is mandatory before any SIU action.
    """

    recommendation_id: str
    claim_id: str
    status: SIURecommendationStatus
    rationale: str = Field(
        description="Human-readable explanation of the SIU referral recommendation"
    )
    priority_factors: list[str] = Field(
        default_factory=list,
        description="Key factors driving the recommendation priority",
    )
    recommended_investigation_types: list[str] = Field(
        default_factory=list,
        description="Suggested SIU investigation actions (advisory only)",
    )
    requires_senior_review: bool = Field(
        default=True,
        description="Always True — SIU referrals require human review before action",
    )
    generated_at: datetime
    source_system: SourceSystem = SourceSystem.FRAUD


# ---------------------------------------------------------------------------
# Provider result wrappers
# ---------------------------------------------------------------------------


class GetFraudIndicatorsResult(BaseModel):
    status: ToolResultStatus
    assessment: FraudAssessment | None = None
    error: ToolError | None = None


class GetSIURecommendationResult(BaseModel):
    status: ToolResultStatus
    recommendation: SIURecommendation | None = None
    error: ToolError | None = None


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class IFraudReadProvider(Protocol):
    """
    Read interface for the fraud detection system.

    All implementations — mock, hybrid, real — must satisfy this protocol.

    ACCESS CONTROL:
      Fraud indicator data is sensitive. Implementations must enforce:
        - Scope: only claims in the adjuster's portfolio
        - Logging: every fraud data access must generate an audit event
        - Role check: 'adjuster' role is sufficient for get_fraud_indicators;
          SIU data (get_siu_recommendation) may require 'senior_adjuster' role

    SPECIFICATION ALIGNMENT (ADR-004):
      Obtain the fraud system API specification from the SIU / Analytics team
      before implementing the real adapter. Fraud systems often use proprietary
      scoring APIs that differ significantly from standard REST conventions.
    """

    def health(self) -> ProviderStatus:
        """Report provider operational status."""
        ...

    def get_fraud_indicators(
        self,
        claim_id: str,
        context: ToolExecutionContext,
    ) -> GetFraudIndicatorsResult:
        """
        Retrieve the fraud assessment and all indicators for a claim.

        Returns NOT_FOUND if no assessment is available (e.g. new claim
        with insufficient history for scoring). Never returns a default
        'low risk' assessment when data is unavailable — the absence of
        data is not the same as the absence of risk.
        """
        ...

    def get_siu_recommendation(
        self,
        claim_id: str,
        context: ToolExecutionContext,
    ) -> GetSIURecommendationResult:
        """
        Retrieve the SIU referral recommendation for a claim.

        The recommendation is advisory. Senior adjuster review is required
        before any SIU referral is initiated. The platform governance engine
        will ESCALATE claims with REFER or URGENT_REFER status.
        """
        ...
