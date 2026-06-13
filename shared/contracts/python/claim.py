"""
Claim domain contracts — Python / Pydantic.
Canonical definitions for claim data crossing layer boundaries.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    PENDING = "PENDING"
    CLOSED = "CLOSED"
    DENIED = "DENIED"


class ClaimType(str, Enum):
    AUTO_LIABILITY = "AUTO_LIABILITY"
    AUTO_PHYSICAL_DAMAGE = "AUTO_PHYSICAL_DAMAGE"
    PROPERTY_DAMAGE = "PROPERTY_DAMAGE"
    WORKERS_COMPENSATION = "WORKERS_COMPENSATION"
    GENERAL_LIABILITY = "GENERAL_LIABILITY"
    MEDICAL_MALPRACTICE = "MEDICAL_MALPRACTICE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PartyRole(str, Enum):
    INSURED = "INSURED"
    CLAIMANT = "CLAIMANT"
    ATTORNEY = "ATTORNEY"
    WITNESS = "WITNESS"
    EXPERT = "EXPERT"


class ClaimParty(BaseModel):
    party_id: str
    role: PartyRole
    name: str
    contact_phone: str | None = None
    contact_email: str | None = None
    represented_by: str | None = None


class Coverage(BaseModel):
    coverage_id: str
    coverage_type: str
    limit: Decimal
    deductible: Decimal
    is_applicable: bool


class ClaimDocument(BaseModel):
    document_id: str
    title: str
    document_type: str
    uploaded_at: datetime
    uploaded_by: str


class ClaimNote(BaseModel):
    note_id: str
    content: str
    author: str
    authored_at: datetime
    is_ai_generated: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None


class Claim(BaseModel):
    claim_id: str
    claim_number: str
    status: ClaimStatus
    type: ClaimType
    risk_level: RiskLevel
    date_of_loss: date
    reported_at: datetime
    description: str
    reserve_amount: Decimal = Field(ge=0)
    paid_amount: Decimal = Field(ge=0)
    parties: list[ClaimParty] = Field(default_factory=list)
    coverages: list[Coverage] = Field(default_factory=list)
    notes: list[ClaimNote] = Field(default_factory=list)
    documents: list[ClaimDocument] = Field(default_factory=list)
    litigation_flag: bool = False
    jurisdiction_code: str


class ClaimListItem(BaseModel):
    """Lightweight projection used in claim list views."""
    claim_id: str
    claim_number: str
    status: ClaimStatus
    type: ClaimType
    risk_level: RiskLevel
    date_of_loss: date
    reserve_amount: Decimal
    primary_insured_name: str
