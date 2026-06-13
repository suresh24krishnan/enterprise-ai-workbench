"""
GovernanceDecision contract — Python / Pydantic.
Represents the outcome of evaluating a request against governance policy.
Every AI action produces exactly one GovernanceDecision before proceeding.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class GovernanceOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


class GovernanceDenyReason(str, Enum):
    POLICY_VIOLATION = "POLICY_VIOLATION"
    INSUFFICIENT_PERMISSION = "INSUFFICIENT_PERMISSION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    PII_EXPOSURE_RISK = "PII_EXPOSURE_RISK"
    HIGH_RISK_ACTION_BLOCKED = "HIGH_RISK_ACTION_BLOCKED"


class GovernanceEscalateReason(str, Enum):
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    HIGH_RESERVE_AMOUNT = "HIGH_RESERVE_AMOUNT"
    LITIGATION_FLAG = "LITIGATION_FLAG"
    LOW_MODEL_CONFIDENCE = "LOW_MODEL_CONFIDENCE"
    SENSITIVE_CONTENT_DETECTED = "SENSITIVE_CONTENT_DETECTED"


class PolicyEvaluation(BaseModel):
    policy_id: str
    policy_version: str
    rule_id: str
    matched: bool
    outcome: GovernanceOutcome
    reason: str


class GovernanceDecision(BaseModel):
    decision_id: str
    evaluated_at: datetime
    task_type: str
    claim_id: str | None = None

    # Final outcome — strictest rule wins (DENY > ESCALATE > ALLOW)
    outcome: GovernanceOutcome

    # Human-readable explanation always present
    reason: str

    deny_reason: GovernanceDenyReason | None = None
    escalate_reason: GovernanceEscalateReason | None = None

    # Individual policy evaluations that led to this decision
    policy_evaluations: list[PolicyEvaluation] = []

    policy_set_id: str
    policy_set_version: str
