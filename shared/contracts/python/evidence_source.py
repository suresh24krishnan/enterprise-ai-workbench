"""
EvidenceSource contract — Python / Pydantic.
Represents a single retrieved knowledge chunk that grounded an AI response.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    CLAIM_DOCUMENT = "CLAIM_DOCUMENT"
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"
    CLAIM_NOTE = "CLAIM_NOTE"
    POLICY_DOCUMENT = "POLICY_DOCUMENT"
    REGULATION = "REGULATION"


class EvidenceSource(BaseModel):
    source_id: str
    source_type: SourceType
    title: str
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    document_id: str | None = None
    page_reference: str | None = None
    retrieved_at: datetime
