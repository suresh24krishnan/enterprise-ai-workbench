"""
AuditEvent contract — Python / Pydantic.
Represents an immutable audit record. Once written, never modified.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from .governance_decision import GovernanceOutcome


class AuditEventType(str, Enum):
    # Session
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    SESSION_EXPIRED = "user.session_expired"

    # Claims
    CLAIM_SELECTED = "claim.selected"
    CLAIM_SEARCHED = "claim.searched"

    # AI — reads
    SUMMARY_GENERATED = "ai.summary.generated"
    CONVERSATION_TURN_COMPLETED = "ai.conversation.turn_completed"
    KNOWLEDGE_RETRIEVED = "ai.rag.retrieved"

    # AI — writes
    NOTE_DRAFTED = "ai.note.drafted"

    # Governance
    GOVERNANCE_EVALUATED = "governance.evaluated"

    # Human decisions
    HUMAN_APPROVAL_REQUESTED = "human.approval.requested"
    HUMAN_APPROVAL_GRANTED = "human.approval.granted"
    HUMAN_APPROVAL_REJECTED = "human.approval.rejected"

    # Writes to external systems
    CLAIM_NOTE_WRITTEN = "claimcenter.note.written"
    CLAIM_NOTE_WRITE_FAILED = "claimcenter.note.write_failed"


class AuditEvent(BaseModel):
    event_id: str                    # UUID, assigned by audit store
    event_type: AuditEventType
    occurred_at: datetime            # UTC

    # Who and where
    user_id: str
    user_role: str
    session_id: str

    # What claim (if applicable)
    claim_id: str | None = None
    claim_number: str | None = None

    # Event-specific payload
    payload: dict[str, Any] = {}

    # Governance context
    governance_decision_id: str | None = None
    governance_outcome: GovernanceOutcome | None = None

    # Model context
    model_id: str | None = None
    task_type: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
