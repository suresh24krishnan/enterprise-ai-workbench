"""
Email and correspondence provider contracts.

Defines the read interface for claim-related email correspondence and
the draft interface for AI-assisted email drafting.

IMPORTANT — Specification alignment (ADR-004):
  The email source system may be Microsoft Exchange / Graph API, a CRM
  system, or ClaimCenter correspondence attachments. Obtain the specification
  before implementing the real adapter.

  Graph API notes:
    - Email retrieval requires Microsoft Graph API (delegated or application
      permissions). OBO identity (ADR-003) is strongly preferred so that
      email access is scoped to the adjuster's mailbox and claim folders.
    - Email content is always untrusted data (ADR-006). Apply structural
      isolation before passing to the AI supervisor.

SEND EMAIL — NOT IMPLEMENTED:
  send_email is intentionally excluded from this contract. Email sending
  is a write operation with external impact (emails leave the organisation)
  and requires:
    - Human review and approval of content before sending
    - Explicit send permission separate from the write gate (ADR-002)
    - Compliance review of AI-generated email content
    - Audit trail with full content capture
  This will be defined in a future sprint as a separate write contract
  with its own gate conditions.

DRAFT EMAIL — INCLUDED:
  draft_email is included as a read-adjacent operation. It uses the AI
  model to draft email text based on claim context. The draft is returned
  to the adjuster for review and manual sending. No email is sent by the
  platform. The draft is advisory only.

CRITICAL — Untrusted content (ADR-006):
  Retrieved email content is UNTRUSTED DATA. Emails may contain injected
  instructions embedded by external parties. Apply structural isolation
  (ADR-006 Layer 1) before passing email body content to the AI supervisor.

ERROR HANDLING (all implementations):
  - 404: no correspondence found for claim → NOT_FOUND
  - 403: adjuster lacks mailbox access → PERMISSION_DENIED
  - 429: rate limit exceeded → RATE_LIMITED (retryable=True)
  - 503: email system unavailable → UNAVAILABLE (retryable=True)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from backend.app.integration.contracts.common import (
    PartySummary,
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)


# ---------------------------------------------------------------------------
# Email-specific enums
# ---------------------------------------------------------------------------


class EmailDirection(str, Enum):
    """Direction of email correspondence relative to the organisation."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


class EmailStatus(str, Enum):
    """Read/processing status of an email."""

    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    FORWARDED = "forwarded"
    ARCHIVED = "archived"


class DraftEmailTone(str, Enum):
    """Requested tone for AI-generated email drafts."""

    FORMAL = "formal"
    PROFESSIONAL = "professional"
    EMPATHETIC = "empathetic"
    FIRM = "firm"


class DraftEmailPurpose(str, Enum):
    """Purpose of a draft email request."""

    ACKNOWLEDGEMENT = "acknowledgement"
    STATUS_UPDATE = "status_update"
    INFORMATION_REQUEST = "information_request"
    COVERAGE_EXPLANATION = "coverage_explanation"
    PAYMENT_NOTIFICATION = "payment_notification"
    DENIAL_EXPLANATION = "denial_explanation"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class EmailSummary(BaseModel):
    """
    Lightweight email record for correspondence lists.

    NOTE: Email body is NOT included in summary records. Use get_email_thread()
    or specific thread retrieval to access content. Email body is untrusted
    data subject to ADR-006 isolation requirements.
    """

    email_id: str
    claim_id: str
    direction: EmailDirection
    status: EmailStatus
    subject: str | None = None
    from_party: PartySummary | None = None
    to_parties: list[PartySummary] = Field(default_factory=list)
    sent_at: datetime | None = None
    received_at: datetime | None = None
    has_attachments: bool = False
    thread_id: str | None = None
    source_system: SourceSystem = SourceSystem.EMAIL


class EmailThread(BaseModel):
    """
    A thread of related email correspondence for a claim.

    UNTRUSTED DATA: Email body content in this record originates from
    external parties (claimants, attorneys, vendors). Apply structural
    isolation (ADR-006 Layer 1) before passing any body content to the
    AI supervisor in an instruction context.
    """

    thread_id: str
    claim_id: str
    subject: str | None = None
    participants: list[PartySummary] = Field(default_factory=list)
    message_count: int = 0
    last_activity: datetime | None = None
    messages: list["EmailMessage"] = Field(
        default_factory=list,
        description=(
            "Email messages in this thread, ordered oldest first. "
            "Body content is UNTRUSTED DATA — ADR-006 applies."
        ),
    )
    source_system: SourceSystem = SourceSystem.EMAIL


class EmailMessage(BaseModel):
    """
    A single email message within a thread.

    UNTRUSTED DATA: body content is external party text.
    Place in [RETRIEVED CONTENT] section only when passing to AI (ADR-006).
    """

    message_id: str
    thread_id: str
    direction: EmailDirection
    status: EmailStatus
    from_party: PartySummary | None = None
    to_parties: list[PartySummary] = Field(default_factory=list)
    subject: str | None = None
    body: str | None = Field(
        default=None,
        description=(
            "Email body text. UNTRUSTED DATA — external party content. "
            "Never place in AI instruction context. "
            "Isolate in [RETRIEVED CONTENT] section (ADR-006 Layer 1)."
        ),
    )
    sent_at: datetime | None = None
    has_attachments: bool = False
    attachment_document_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Draft request/response models
# ---------------------------------------------------------------------------


class DraftEmailRequest(BaseModel):
    """
    Request for an AI-generated email draft.

    The AI supervisor produces a draft based on claim context. The draft
    is returned to the adjuster for review and manual sending.
    No email is sent by the platform.
    """

    claim_id: str
    purpose: DraftEmailPurpose
    recipient: PartySummary | None = None
    tone: DraftEmailTone = DraftEmailTone.PROFESSIONAL
    key_points: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Key points the adjuster wants the draft to cover",
    )
    reference_thread_id: str | None = Field(
        default=None,
        description="Thread ID to use as context for the draft (prior correspondence)",
    )
    additional_context: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional adjuster-provided context for the draft",
    )


class DraftEmailResult(BaseModel):
    """
    Result of an AI email draft request.

    The draft is advisory only. The adjuster reviews and sends manually.
    The platform does not send emails.
    """

    status: ToolResultStatus
    draft_subject: str | None = None
    draft_body: str | None = Field(
        default=None,
        description=(
            "AI-generated draft email body. Advisory only — adjuster must "
            "review before sending. Platform does not send emails."
        ),
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="AI confidence in the draft quality",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Adjuster attention flags, e.g. 'Coverage position not yet confirmed'",
    )
    error: ToolError | None = None


# ---------------------------------------------------------------------------
# Provider result wrappers
# ---------------------------------------------------------------------------


class GetClaimCorrespondenceResult(BaseModel):
    status: ToolResultStatus
    emails: list[EmailSummary] = Field(default_factory=list)
    total_count: int = 0
    error: ToolError | None = None


class GetEmailThreadResult(BaseModel):
    status: ToolResultStatus
    thread: EmailThread | None = None
    error: ToolError | None = None


# ---------------------------------------------------------------------------
# Provider protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class IEmailReadProvider(Protocol):
    """
    Read interface for claim email correspondence.

    All implementations — mock, hybrid, real — must satisfy this protocol.

    UNTRUSTED CONTENT (ADR-006):
      Implementations must return email body text as opaque string data.
      The orchestration layer is responsible for structural isolation
      before any body content reaches the AI supervisor.

    SPECIFICATION ALIGNMENT (ADR-004):
      The real adapter must be derived from the Microsoft Graph API specification
      (or the applicable email system API). OBO identity (ADR-003) is required
      so email access is scoped to the adjuster's mailbox.
    """

    def health(self) -> ProviderStatus:
        """Report provider operational status."""
        ...

    def get_claim_correspondence(
        self,
        claim_id: str,
        context: ToolExecutionContext,
        direction_filter: EmailDirection | None = None,
        max_results: int = 20,
    ) -> GetClaimCorrespondenceResult:
        """
        List email correspondence associated with a claim.
        Body content is not included in summary records.
        """
        ...

    def get_email_thread(
        self,
        thread_id: str,
        claim_id: str,
        context: ToolExecutionContext,
    ) -> GetEmailThreadResult:
        """
        Retrieve a complete email thread with message bodies.

        claim_id is required for scope enforcement — a thread may only
        be retrieved if it is associated with this specific claim.

        UNTRUSTED DATA: Returned body content must be placed in the
        [RETRIEVED CONTENT] section of any AI prompt (ADR-006 Layer 1).
        """
        ...


@runtime_checkable
class IEmailDraftProvider(Protocol):
    """
    Draft interface for AI-assisted email composition.

    Draft email is a read-adjacent operation — the AI supervisor generates
    draft text based on claim context. No email is sent by the platform.
    The adjuster reviews the draft and sends manually.

    SEND EMAIL IS NOT IMPLEMENTED. It will be defined in a future sprint
    as a write operation with its own gate conditions separate from
    the ClaimCenter write gate (ADR-002).
    """

    def draft_email(
        self,
        request: DraftEmailRequest,
        context: ToolExecutionContext,
    ) -> DraftEmailResult:
        """
        Generate an AI draft email based on claim context and adjuster input.

        Returns advisory draft text only. No email is sent.
        The adjuster is responsible for reviewing and sending.
        """
        ...
