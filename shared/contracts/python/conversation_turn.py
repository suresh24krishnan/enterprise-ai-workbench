"""
ConversationTurn contract — Python / Pydantic.
Represents a single user/assistant exchange within a scoped claim conversation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from .evidence_source import EvidenceSource
from .governance_decision import GovernanceDecision
from .model_route_decision import ModelRouteDecision


class TurnRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class TurnStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DENIED = "DENIED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ConversationTurn(BaseModel):
    turn_id: str
    conversation_id: str
    claim_id: str
    sequence_number: int              # 1-based, monotonically increasing
    role: TurnRole
    status: TurnStatus
    created_at: datetime

    # User input
    user_message: str

    # AI output (None if denied or pending)
    assistant_message: str | None = None

    # Grounding
    evidence_sources: list[EvidenceSource] = []

    # Governance and routing (populated when role = ASSISTANT)
    governance_decision: GovernanceDecision | None = None
    model_route_decision: ModelRouteDecision | None = None

    # Audit
    audit_event_id: str | None = None


class Conversation(BaseModel):
    conversation_id: str
    claim_id: str
    user_id: str
    status: Literal["ACTIVE", "CLOSED", "PENDING_APPROVAL"]
    started_at: datetime
    updated_at: datetime
    turns: list[ConversationTurn] = []
