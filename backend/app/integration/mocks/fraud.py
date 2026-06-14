"""
Mock fraud detection provider — specification-shaped simulation.

Implements IFraudReadProvider with a low-risk fraud assessment for
CLM-2026-100245 (ABC Logistics / rear-end collision / no prior fraud history).

IMPORTANT — Specification alignment (ADR-004):
  The real fraud adapter must be derived from the fraud system API spec.
  Fraud systems often use proprietary scoring APIs (FRISS, Shift Technology,
  or an internal model). Confirm the interface type before building.
  Key mappings to confirm:
    Claim ID field in fraud API (may differ from ClaimCenter claim number)
    Score scale (confirm 0–100 vs. other range)
    Indicator codes (system-specific, must be mapped to FraudIndicatorType)
    SIU recommendation status codes

Fraud assessments are advisory — they do not constitute a finding of fraud.
All fraud determinations and SIU referrals require human review.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from backend.app.integration.contracts.common import (
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)
from backend.app.integration.contracts.fraud import (
    FraudAssessment,
    FraudIndicator,
    FraudIndicatorType,
    FraudRiskLevel,
    GetFraudIndicatorsResult,
    GetSIURecommendationResult,
    IFraudReadProvider,
    SIURecommendation,
    SIURecommendationStatus,
)
from backend.app.integration.mocks.simulation import SimulationConfig, apply_simulation

_CLAIM_ID = "CLM-2026-100245"
_CUSTOMER_ID = "EDW-CUST-10042"

_INDICATORS = [
    FraudIndicator(
        indicator_id="fi-001",
        claim_id=_CLAIM_ID,
        indicator_type=FraudIndicatorType.LATE_REPORTING,
        description="Claim reported same day as loss — no late reporting detected.",
        confidence=Decimal("0.05"),
        detected_at=datetime(2026, 6, 13, 9, 30, 0),
        source_system=SourceSystem.FRAUD,
        supporting_evidence=["Loss date 2026-06-08, reported 2026-06-08"],
    ),
    FraudIndicator(
        indicator_id="fi-002",
        claim_id=_CLAIM_ID,
        indicator_type=FraudIndicatorType.PRIOR_CLAIM_PATTERN,
        description=(
            "Customer has 4 prior claims over 6 years — within expected range "
            "for a commercial fleet operator. No unusual pattern detected."
        ),
        confidence=Decimal("0.08"),
        detected_at=datetime(2026, 6, 13, 9, 30, 0),
        source_system=SourceSystem.FRAUD,
        supporting_evidence=["EDW customer profile — 4 lifetime claims"],
    ),
]

_ASSESSMENT = FraudAssessment(
    assessment_id="fa-CLM-2026-100245",
    claim_id=_CLAIM_ID,
    risk_level=FraudRiskLevel.LOW,
    fraud_score=Decimal("14.0"),
    indicators=_INDICATORS,
    assessed_at=datetime(2026, 6, 13, 9, 30, 0),
    model_version="fraud-model-v2.4-mock",
    siu_recommendation=SIURecommendationStatus.NO_REFERRAL,
    prior_fraud_flags_on_customer=0,
    source_system=SourceSystem.FRAUD,
)

_SIU_RECOMMENDATION = SIURecommendation(
    recommendation_id="siu-CLM-2026-100245",
    claim_id=_CLAIM_ID,
    status=SIURecommendationStatus.NO_REFERRAL,
    rationale=(
        "Claim presents no indicators warranting SIU referral. Police report "
        "establishes third-party liability. Damage is consistent with photographic "
        "evidence. Customer has no prior fraud flags or SIU history."
    ),
    priority_factors=[],
    recommended_investigation_types=[],
    requires_senior_review=True,
    generated_at=datetime(2026, 6, 13, 9, 30, 0),
    source_system=SourceSystem.FRAUD,
)


class MockFraudProvider:
    """
    Specification-shaped mock for fraud detection read access.

    Returns a low-risk assessment for CLM-2026-100245.
    Returns NOT_FOUND for all other claim IDs.

    NOTE — Specification alignment (ADR-004):
      Fraud system APIs vary significantly by vendor. Obtain the spec
      from the SIU / Analytics team before building the real adapter.
    """

    def __init__(self, sim: SimulationConfig | None = None) -> None:
        self._sim = sim or SimulationConfig()

    def health(self) -> ProviderStatus:
        return ProviderStatus.MOCK

    def get_fraud_indicators(
        self, claim_id: str, context: ToolExecutionContext
    ) -> GetFraudIndicatorsResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetFraudIndicatorsResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(
                    code="NOT_FOUND",
                    message=f"No fraud assessment available for claim '{claim_id}'.",
                    source_system=SourceSystem.FRAUD,
                    retryable=False,
                ),
            )
        return GetFraudIndicatorsResult(
            status=ToolResultStatus.SUCCESS, assessment=_ASSESSMENT
        )

    def get_siu_recommendation(
        self, claim_id: str, context: ToolExecutionContext
    ) -> GetSIURecommendationResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetSIURecommendationResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(
                    code="NOT_FOUND",
                    message=f"No SIU recommendation available for claim '{claim_id}'.",
                    source_system=SourceSystem.FRAUD,
                    retryable=False,
                ),
            )
        return GetSIURecommendationResult(
            status=ToolResultStatus.SUCCESS, recommendation=_SIU_RECOMMENDATION
        )
