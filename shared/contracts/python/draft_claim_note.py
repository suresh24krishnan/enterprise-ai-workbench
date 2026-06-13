"""
DraftClaimNote contract — Python / Pydantic.
Represents an AI-generated note draft awaiting human review and approval.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from .evidence_source import EvidenceSource
from .governance_decision import GovernanceDecision
from .model_route_decision import ModelRouteDecision


class DraftNoteStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WRITTEN = "WRITTEN"
    WRITE_FAILED = "WRITE_FAILED"


class NoteCategory(str, Enum):
    PROGRESS_NOTE = "PROGRESS_NOTE"
    COVERAGE_ANALYSIS = "COVERAGE_ANALYSIS"
    LIABILITY_ASSESSMENT = "LIABILITY_ASSESSMENT"
    RESERVE_JUSTIFICATION = "RESERVE_JUSTIFICATION"
    CLOSING_NOTE = "CLOSING_NOTE"
    ESCALATION_NOTE = "ESCALATION_NOTE"


class DraftClaimNote(BaseModel):
    draft_id: str
    claim_id: str
    conversation_id: str | None = None
    status: DraftNoteStatus
    category: NoteCategory
    created_at: datetime
    updated_at: datetime

    # AI-generated content
    ai_content: str

    # Human-edited content (starts as copy of ai_content)
    edited_content: str

    # Grounding
    evidence_sources: list[EvidenceSource] = []

    # Governance — always ESCALATE for draft_note task type
    governance_decision: GovernanceDecision
    model_route_decision: ModelRouteDecision

    # Human decision
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    reviewer_comments: str | None = None

    # Write outcome
    claim_center_note_id: str | None = None
    write_attempted_at: datetime | None = None
    write_failure_reason: str | None = None
