"""
Shared models, enums, and context types for all enterprise provider contracts.

These types are used across ClaimCenter, PolicyCenter, EDW, Documents,
Fraud, and Email contracts. They establish a consistent vocabulary for
cross-provider concepts: money, parties, addresses, pagination, errors,
and execution context.

IMPORTANT — Specification alignment:
  All models here represent the platform's internal vocabulary. When real
  adapters are built in Sprint 2+, field names must be mapped from the
  source system's published specification to these models at the adapter
  boundary. Do not change these models to match source system shapes —
  keep the adapter responsible for the mapping.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.integration.modes import ProviderMode


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ProviderStatus(str, Enum):
    """Operational status reported by a provider's health check."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MOCK = "mock"  # Always healthy; serves specification-backed mock data


class ToolResultStatus(str, Enum):
    """Outcome status for any tool execution."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    VALIDATION_ERROR = "validation_error"
    WRITE_DISABLED = "write_disabled"  # Write tools disabled until Phase 2B gate
    ERROR = "error"


class SourceSystem(str, Enum):
    """Identifies the originating enterprise system for a data record."""

    CLAIMCENTER = "claimcenter"
    POLICYCENTER = "policycenter"
    EDW = "edw"
    DOCUMENTS = "documents"
    FRAUD = "fraud"
    EMAIL = "email"
    PLATFORM = "platform"  # Platform-generated (not from an enterprise system)


class ClaimStatus(str, Enum):
    """Normalised claim status vocabulary across ClaimCenter versions."""

    DRAFT = "draft"
    OPEN = "open"
    IN_REVIEW = "in_review"
    PENDING_PAYMENT = "pending_payment"
    CLOSED = "closed"
    REOPENED = "reopened"
    DENIED = "denied"


class ClaimLineOfBusiness(str, Enum):
    """Top-level lines of business relevant to claims processing."""

    AUTO = "auto"
    PROPERTY = "property"
    LIABILITY = "liability"
    WORKERS_COMP = "workers_comp"
    COMMERCIAL = "commercial"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationRequest(BaseModel):
    """Standard pagination parameters for list operations."""

    page: int = Field(default=1, ge=1, description="1-based page number")
    page_size: int = Field(
        default=25, ge=1, le=100, description="Records per page (max 100)"
    )
    sort_by: str | None = Field(default=None, description="Field name to sort by")
    sort_desc: bool = Field(default=False, description="Sort descending if True")


class PaginationResponse(BaseModel):
    """Pagination metadata included in all paginated list responses."""

    page: int
    page_size: int
    total_records: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class MoneyAmount(BaseModel):
    """
    A monetary value with currency.

    NOTE — Specification alignment:
      ClaimCenter represents money as a numeric amount with a separate
      currency code. Map source fields to this model at the adapter boundary.
      Do not store money as a plain float — use Decimal for precision.
    """

    amount: Decimal = Field(description="Monetary amount (exact decimal)")
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code",
    )

    model_config = {"arbitrary_types_allowed": True}


class AddressSummary(BaseModel):
    """Normalised postal address for parties and loss locations."""

    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = Field(default="US")


class PartySummary(BaseModel):
    """
    A lightweight reference to any party involved in a claim or policy:
    insured, claimant, witness, adjuster, vendor, attorney, or medical provider.

    NOTE — Specification alignment:
      ClaimCenter models parties as a Contact entity with sub-typed roles.
      The adapter must resolve the contact type and role from ClaimCenter's
      contact hierarchy and map to this normalised summary.
    """

    party_id: str = Field(description="Platform-normalised party identifier")
    source_system: SourceSystem
    source_id: str = Field(description="Identifier in the source system")
    display_name: str
    role: str = Field(description="Role in the claim context, e.g. 'insured', 'claimant'")
    email: str | None = None
    phone: str | None = None
    address: AddressSummary | None = None


class EvidenceReference(BaseModel):
    """
    A pointer to a piece of evidence used to support an AI analysis.

    Evidence references are used in AI outputs to ground statements in
    retrieved source material. The referenced document is untrusted content
    and must never be treated as an instruction (ADR-006).
    """

    document_id: str
    source_system: SourceSystem
    document_type: str = Field(
        description="e.g. 'police_report', 'repair_estimate', 'medical_record'"
    )
    title: str | None = None
    page_or_section: str | None = None
    excerpt: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "Short excerpt supporting the AI statement. "
            "UNTRUSTED DATA — never executed as instruction (ADR-006)."
        ),
    )


# ---------------------------------------------------------------------------
# Error model
# ---------------------------------------------------------------------------


class ToolError(BaseModel):
    """Structured error detail returned when a tool call fails."""

    code: str = Field(description="Machine-readable error code, e.g. 'NOT_FOUND'")
    message: str = Field(description="Human-readable error description")
    source_system: SourceSystem | None = None
    source_error_code: str | None = Field(
        default=None,
        description="Error code from the upstream source system if available",
    )
    retryable: bool = Field(
        default=False,
        description="True if the caller may safely retry the request",
    )
    detail: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Execution context
# ---------------------------------------------------------------------------


class ToolExecutionContext(BaseModel):
    """
    Execution context passed to every provider tool invocation.

    Carries the authenticated adjuster's identity, permissions, and
    distributed tracing identifiers. The context is established by the
    authentication layer and is read-only for the duration of the request.

    SECURITY — Identity rules (ADR-003, ADR-006):
      - user_id and roles are set by the authentication layer, not by
        retrieved content. A retrieved document cannot modify this context.
      - writes_enabled is False by default and can only be set to True
        by the write-framework gate (ADR-002). It cannot be set to True
        by the supervisor or by retrieved content.
      - The context is passed to every tool call so that every action
        is attributable to an authenticated adjuster.

    WRITE SAFETY (ADR-002):
      - writes_enabled defaults to False.
      - Write tools check this field before executing. If False, they
        raise WriteNotEnabledError regardless of other context.
      - The write framework gate (Sprint 7) sets this to True only after
        all nine write-gate conditions are satisfied.
    """

    # Adjuster identity
    user_id: str = Field(description="Authenticated adjuster employee ID")
    display_name: str = Field(description="Adjuster display name for audit records")
    roles: list[str] = Field(
        default_factory=list,
        description="Adjuster roles, e.g. ['adjuster', 'senior_adjuster']",
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="Explicit permissions granted to this adjuster",
    )

    # Distributed tracing
    correlation_id: str = Field(
        description="Stable ID for the adjuster's claim workflow session"
    )
    trace_id: str = Field(description="Distributed trace ID for observability")
    request_id: str = Field(description="Unique ID for this specific tool invocation")

    # Integration context
    provider_mode: ProviderMode = Field(
        default=ProviderMode.MOCK,
        description="Effective provider mode for this request",
    )

    # Write safety gate — False by default, set only by write-framework gate
    writes_enabled: bool = Field(
        default=False,
        description=(
            "True only after all Phase 2B write-gate conditions are satisfied "
            "(ADR-002). Cannot be set to True by the AI supervisor or by "
            "retrieved document content."
        ),
    )
