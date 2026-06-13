"""
ClaimSummary contract — Python / Pydantic.
Represents the governed AI-generated summary of a claim.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .evidence_source import EvidenceSource
from .governance_decision import GovernanceDecision
from .model_route_decision import ModelRouteDecision


class ClaimSummary(BaseModel):
    summary_id: str
    claim_id: str
    generated_at: datetime

    # Core AI output
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    coverage_analysis: str
    recommended_actions: list[str] = Field(default_factory=list)

    # Grounding and provenance
    evidence_sources: list[EvidenceSource] = Field(default_factory=list)

    # Governance and routing metadata
    governance_decision: GovernanceDecision
    model_route_decision: ModelRouteDecision

    # Confidence
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_rationale: str
