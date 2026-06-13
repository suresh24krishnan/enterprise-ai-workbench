"""
ModelRouteDecision contract — Python / Pydantic.
Represents the model router's selection decision for a given task.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TaskType(str, Enum):
    CLAIM_SUMMARY = "claim_summary"
    CLAIM_QA = "claim_qa"
    DRAFT_NOTE = "draft_note"
    GOVERNANCE_CHECK = "governance_check"
    AUDIT_EXPLANATION = "audit_explanation"
    HIGH_RISK_ESCALATION = "high_risk_escalation"


class ModelTier(str, Enum):
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    MOCK = "MOCK"


class RoutingReason(str, Enum):
    TASK_TYPE_DEFAULT = "TASK_TYPE_DEFAULT"
    HIGH_RISK_CLAIM = "HIGH_RISK_CLAIM"
    LOW_CONFIDENCE_REROUTE = "LOW_CONFIDENCE_REROUTE"
    PROVIDER_FAILOVER = "PROVIDER_FAILOVER"
    COST_THRESHOLD_OVERRIDE = "COST_THRESHOLD_OVERRIDE"


class ModelRouteDecision(BaseModel):
    route_id: str
    decided_at: datetime
    task_type: TaskType

    # Selected model
    model_id: str           # e.g. "claude-sonnet-4-6" or "mock-standard"
    model_tier: ModelTier
    provider_id: str        # e.g. "anthropic", "azure_openai", "mock"

    # Why this model was chosen
    routing_reason: RoutingReason
    routing_rationale: str

    # Routing inputs
    claim_risk_level: str | None = None
    estimated_cost: float | None = None
    actual_cost: float | None = None

    # Fallback
    primary_model_id: str | None = None
    fallback_reason: str | None = None
