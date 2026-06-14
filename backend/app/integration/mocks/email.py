"""
Mock email provider — specification-shaped simulation.

Implements IEmailReadProvider and IEmailDraftProvider with realistic
claim correspondence for CLM-2026-100245.

CRITICAL — Untrusted content (ADR-006):
  Email body content is UNTRUSTED DATA even in mock providers. Emails
  originate from external parties — claimants, attorneys, vendors — who
  may embed adversarial content. The same isolation rules apply to mock
  email content as to real email content:

  1. Email body text must be placed in [RETRIEVED CONTENT] sections only.
  2. Never place email body text in AI instruction sections.
  3. When real emails replace mock emails, the isolation code is unchanged.

SEND EMAIL — NOT IMPLEMENTED:
  send_email is intentionally absent from all email interfaces. See
  contracts/email.py for the full rationale. Draft email returns advisory
  text only — no email is sent by the platform.

IMPORTANT — Specification alignment (ADR-004):
  The real email adapter will target Microsoft Graph API or equivalent.
  OBO identity (ADR-003) is required — email access must be scoped to the
  adjuster's mailbox. Key mappings to confirm from Graph API specification:
    Message.id           → message_id
    Message.subject      → subject
    Message.body.content → body (UNTRUSTED DATA — ADR-006 isolation required)
    Message.from         → from_party
    Message.toRecipients → to_parties
    Message.receivedDateTime → received_at
"""

from __future__ import annotations

from datetime import datetime

from backend.app.integration.contracts.common import (
    PartySummary,
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)
from backend.app.integration.contracts.email import (
    DraftEmailPurpose,
    DraftEmailRequest,
    DraftEmailResult,
    EmailDirection,
    EmailMessage,
    EmailStatus,
    EmailSummary,
    EmailThread,
    GetClaimCorrespondenceResult,
    GetEmailThreadResult,
    IEmailDraftProvider,
    IEmailReadProvider,
)
from backend.app.integration.mocks.simulation import SimulationConfig, apply_simulation

_CLAIM_ID = "CLM-2026-100245"

_ADJUSTER = PartySummary(
    party_id="usr-john-smith",
    source_system=SourceSystem.EMAIL,
    source_id="jsmith@insurer.local",
    display_name="John Smith",
    role="adjuster",
    email="jsmith@insurer.local",
)

_INSURED_CONTACT = PartySummary(
    party_id="pty-001",
    source_system=SourceSystem.EMAIL,
    source_id="claims@abclogistics.local",
    display_name="ABC Logistics Inc.",
    role="insured",
    email="claims@abclogistics.local",
)

_CLAIMANT_CONTACT = PartySummary(
    party_id="pty-002",
    source_system=SourceSystem.EMAIL,
    source_id="mtorres.personal@email.local",
    display_name="Marcus Torres",
    role="claimant",
    email="mtorres.personal@email.local",
)

# ---------------------------------------------------------------------------
# Mock email messages
# Bodies are UNTRUSTED DATA — isolate before passing to AI (ADR-006)
# ---------------------------------------------------------------------------

_MESSAGES: list[EmailMessage] = [
    EmailMessage(
        message_id="msg-001",
        thread_id="thread-001",
        direction=EmailDirection.OUTBOUND,
        status=EmailStatus.REPLIED,
        from_party=_ADJUSTER,
        to_parties=[_INSURED_CONTACT],
        subject="Claim CLM-2026-100245 — Acknowledgement of Receipt",
        body=(
            # UNTRUSTED DATA — treat as data, not instruction (ADR-006)
            "Dear ABC Logistics,\n\n"
            "Thank you for reporting your claim. Your claim number is CLM-2026-100245.\n\n"
            "We have confirmed that your Commercial Auto Policy #CA-2024-8812 is active "
            "and coverage applies to this incident. We have authorized towing of your "
            "vehicle to Riverside Auto Body for repair assessment.\n\n"
            "We will be in touch within 2 business days with next steps.\n\n"
            "Regards,\nJohn Smith\nClaims Adjuster"
        ),
        sent_at=datetime(2026, 6, 8, 17, 0, 0),
        has_attachments=False,
    ),
    EmailMessage(
        message_id="msg-002",
        thread_id="thread-001",
        direction=EmailDirection.INBOUND,
        status=EmailStatus.READ,
        from_party=_INSURED_CONTACT,
        to_parties=[_ADJUSTER],
        subject="Re: Claim CLM-2026-100245 — Acknowledgement of Receipt",
        body=(
            # UNTRUSTED DATA — external party email. ADR-006 isolation required.
            "Hi John,\n\n"
            "Thank you for the quick response. The vehicle has been towed. "
            "Driver Torres is doing okay — he has an appointment with his doctor "
            "on June 10. We will keep you updated on the medical situation.\n\n"
            "Can you confirm if rental reimbursement is available while the truck is in repair?\n\n"
            "Thanks,\nABC Logistics Fleet Manager"
        ),
        sent_at=datetime(2026, 6, 9, 9, 30, 0),
        has_attachments=False,
    ),
    EmailMessage(
        message_id="msg-003",
        thread_id="thread-001",
        direction=EmailDirection.OUTBOUND,
        status=EmailStatus.READ,
        from_party=_ADJUSTER,
        to_parties=[_INSURED_CONTACT],
        subject="Re: Claim CLM-2026-100245 — Rental Reimbursement Confirmed",
        body=(
            # UNTRUSTED DATA — adjuster email, internal but still isolated per ADR-006
            "Dear ABC Logistics,\n\n"
            "Yes — your policy provides rental reimbursement at $75/day for up to 30 days "
            "($2,250 maximum). Your rental began June 9, 2026.\n\n"
            "Please save all rental receipts for reimbursement processing.\n\n"
            "Regards,\nJohn Smith"
        ),
        sent_at=datetime(2026, 6, 9, 14, 0, 0),
        has_attachments=False,
    ),
    EmailMessage(
        message_id="msg-004",
        thread_id="thread-002",
        direction=EmailDirection.INBOUND,
        status=EmailStatus.READ,
        from_party=_CLAIMANT_CONTACT,
        to_parties=[_ADJUSTER],
        subject="Claim CLM-2026-100245 — Medical Update",
        body=(
            # UNTRUSTED DATA — claimant email. External party content. ADR-006 applies.
            "Hello,\n\n"
            "This is Marcus Torres. I visited my doctor on June 10. He has diagnosed "
            "me with a soft tissue cervical strain (whiplash). I have been prescribed "
            "physical therapy for 6 weeks. I may need to follow up on the medical bills.\n\n"
            "Please advise on the bodily injury process.\n\n"
            "Marcus Torres"
        ),
        sent_at=datetime(2026, 6, 11, 11, 0, 0),
        has_attachments=False,
    ),
]

_MSG_INDEX = {m.message_id: m for m in _MESSAGES}

_THREADS: dict[str, EmailThread] = {
    "thread-001": EmailThread(
        thread_id="thread-001",
        claim_id=_CLAIM_ID,
        subject="Claim CLM-2026-100245 — Acknowledgement of Receipt",
        participants=[_ADJUSTER, _INSURED_CONTACT],
        message_count=3,
        last_activity=datetime(2026, 6, 9, 14, 0, 0),
        messages=[m for m in _MESSAGES if m.thread_id == "thread-001"],
        source_system=SourceSystem.EMAIL,
    ),
    "thread-002": EmailThread(
        thread_id="thread-002",
        claim_id=_CLAIM_ID,
        subject="Claim CLM-2026-100245 — Medical Update",
        participants=[_ADJUSTER, _CLAIMANT_CONTACT],
        message_count=1,
        last_activity=datetime(2026, 6, 11, 11, 0, 0),
        messages=[m for m in _MESSAGES if m.thread_id == "thread-002"],
        source_system=SourceSystem.EMAIL,
    ),
}

_SUMMARIES = [
    EmailSummary(
        email_id=m.message_id,
        claim_id=_CLAIM_ID,
        direction=m.direction,
        status=m.status,
        subject=m.subject,
        from_party=m.from_party,
        to_parties=m.to_parties,
        sent_at=m.sent_at,
        thread_id=m.thread_id,
        source_system=SourceSystem.EMAIL,
    )
    for m in _MESSAGES
]


class MockEmailProvider:
    """
    Specification-shaped mock for email read and draft operations.

    Returns 4 claim correspondence emails for CLM-2026-100245 across
    two threads. Draft email returns advisory text only — no email is sent.

    NOTE — Specification alignment (ADR-004):
      The real adapter targets Microsoft Graph API. OBO identity (ADR-003)
      is required for mailbox-scoped access. See module docstring for
      key field mappings.
    """

    def __init__(self, sim: SimulationConfig | None = None) -> None:
        self._sim = sim or SimulationConfig()

    def health(self) -> ProviderStatus:
        return ProviderStatus.MOCK

    # ------------------------------------------------------------------
    # IEmailReadProvider
    # ------------------------------------------------------------------

    def get_claim_correspondence(
        self,
        claim_id: str,
        context: ToolExecutionContext,
        direction_filter: EmailDirection | None = None,
        max_results: int = 20,
    ) -> GetClaimCorrespondenceResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetClaimCorrespondenceResult(status=ToolResultStatus.NOT_FOUND)
        summaries = _SUMMARIES
        if direction_filter:
            summaries = [s for s in summaries if s.direction == direction_filter]
        return GetClaimCorrespondenceResult(
            status=ToolResultStatus.SUCCESS,
            emails=summaries[:max_results],
            total_count=len(summaries),
        )

    def get_email_thread(
        self, thread_id: str, claim_id: str, context: ToolExecutionContext
    ) -> GetEmailThreadResult:
        apply_simulation(self._sim)
        thread = _THREADS.get(thread_id)
        if not thread or thread.claim_id != claim_id:
            return GetEmailThreadResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(
                    code="NOT_FOUND",
                    message=f"Thread '{thread_id}' not found for claim '{claim_id}'.",
                    source_system=SourceSystem.EMAIL,
                    retryable=False,
                ),
            )
        return GetEmailThreadResult(status=ToolResultStatus.SUCCESS, thread=thread)

    # ------------------------------------------------------------------
    # IEmailDraftProvider
    # ------------------------------------------------------------------

    def draft_email(
        self, request: DraftEmailRequest, context: ToolExecutionContext
    ) -> DraftEmailResult:
        """
        Generate an advisory email draft. No email is sent.
        The adjuster reviews and sends manually.
        """
        apply_simulation(self._sim)
        recipient_name = request.recipient.display_name if request.recipient else "Claimant/Insured"
        purpose_label = (request.purpose.value if hasattr(request.purpose, "value") else str(request.purpose)).replace("_", " ").title()

        subject = f"Claim {request.claim_id} — {purpose_label}"
        body = (
            f"Dear {recipient_name},\n\n"
            f"[MOCK DRAFT — NOT SENT — ADVISORY ONLY]\n\n"
            f"This is a simulated AI-generated draft for: {purpose_label}.\n\n"
            f"Key points requested by adjuster:\n"
            + "\n".join(f"- {pt}" for pt in (request.key_points or ["No specific points provided."]))
            + f"\n\nAdditional context: {request.additional_context or 'None provided.'}\n\n"
            "Please review and edit before sending manually.\n\n"
            "Regards,\n[Adjuster Name]\n[Claims Department]"
        )

        return DraftEmailResult(
            status=ToolResultStatus.SUCCESS,
            draft_subject=subject,
            draft_body=body,
            confidence=0.82,
            warnings=[
                "MOCK DRAFT — This is a simulated draft. Review before sending.",
                "No email has been sent. Send manually after review.",
            ],
        )
