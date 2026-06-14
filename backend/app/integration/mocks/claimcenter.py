"""
Mock ClaimCenter provider — specification-shaped simulation.

Implements IClaimCenterReadProvider and IClaimCenterWriteProvider using
Phase 1 claim data for CLM-2026-100245 (ABC Logistics / Commercial Auto /
rear-end collision).

IMPORTANT — Specification alignment (ADR-004):
  This mock returns data in the platform's normalised vocabulary (snake_case
  field names, ProviderMode enums, MoneyAmount models). When the real
  ClaimCenter adapter is built, it will map Guidewire's field names
  (claimNumber, amountValue, openDate, etc.) to these same models at the
  adapter boundary. The models here are the stable target — not the source.

  Real adapter field mappings to confirm from Guidewire ClaimCenter REST API v10:
    claimNumber         → claim_number
    openDate            → loss_date (date only, not datetime)
    closeDate           → closed_date
    amountValue.amount  → MoneyAmount.amount (Decimal)
    amountValue.currency → MoneyAmount.currency
    assignedUser.publicID → assigned_adjuster_id
    Contact.displayName   → PartySummary.display_name

WRITES DISABLED (ADR-002 Phase 2B):
  All write methods raise MockWriteDisabledError. This is intentional.
  See errors.py and ADR-002 for the nine write-gate conditions.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from backend.app.integration.contracts.claimcenter import (
    ActivitySummary,
    ActivityType,
    ClaimDetail,
    ClaimNote,
    ClaimSummary,
    CreateActivityRequest,
    CreateClaimNoteRequest,
    ExposureSummary,
    ExposureStatus,
    GetActivitiesResult,
    GetClaimNotesResult,
    GetClaimResult,
    GetClaimsResult,
    GetExposuresResult,
    GetPaymentsResult,
    GetReservesResult,
    IClaimCenterReadProvider,
    IClaimCenterWriteProvider,
    NoteType,
    PaymentSummary,
    ReserveSummary,
    ReserveType,
    WriteOperationResult,
)
from backend.app.integration.contracts.common import (
    AddressSummary,
    ClaimLineOfBusiness,
    ClaimStatus,
    MoneyAmount,
    PaginationRequest,
    PartySummary,
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)
from backend.app.integration.mocks.errors import MockNotFoundError, MockWriteDisabledError
from backend.app.integration.mocks.simulation import SimulationConfig, apply_simulation, paginate

# ---------------------------------------------------------------------------
# Canonical claim ID used throughout Phase 1 and Phase 2 mock data
# ---------------------------------------------------------------------------

_CLAIM_ID = "CLM-2026-100245"

# ---------------------------------------------------------------------------
# Static mock data — enterprise-realistic, grounded in Phase 1 scenario
# ---------------------------------------------------------------------------

_INSURED = PartySummary(
    party_id="pty-001",
    source_system=SourceSystem.CLAIMCENTER,
    source_id="CC-CONTACT-10042",
    display_name="ABC Logistics Inc.",
    role="insured",
    email="claims@abclogistics.local",
    phone="305-555-0192",
    address=AddressSummary(
        line1="1400 NW 107th Ave", city="Miami", state="FL", postal_code="33172"
    ),
)

_CLAIMANT = PartySummary(
    party_id="pty-002",
    source_system=SourceSystem.CLAIMCENTER,
    source_id="CC-CONTACT-10043",
    display_name="Marcus Torres",
    role="claimant",
    phone="305-555-0347",
    address=AddressSummary(city="Miami", state="FL"),
)

_LOSS_LOCATION = AddressSummary(
    line1="I-75 & Exit 42", city="Miami", state="FL", postal_code="33150"
)

_CLAIM_SUMMARY = ClaimSummary(
    claim_id=_CLAIM_ID,
    claim_number=_CLAIM_ID,
    policy_number="CA-2024-8812",
    line_of_business=ClaimLineOfBusiness.COMMERCIAL,
    status=ClaimStatus.OPEN,
    loss_date=date(2026, 6, 8),
    reported_date=date(2026, 6, 8),
    insured=_INSURED,
    loss_location=_LOSS_LOCATION,
    loss_cause="Rear-end collision — third party at fault (FL Statute 316.0895)",
    total_incurred=MoneyAmount(amount=Decimal("8450.00"), currency="USD"),
    assigned_adjuster_id="usr-john-smith",
    source_system=SourceSystem.CLAIMCENTER,
)

_CLAIM_DETAIL = ClaimDetail(
    claim_id=_CLAIM_ID,
    claim_number=_CLAIM_ID,
    policy_number="CA-2024-8812",
    line_of_business=ClaimLineOfBusiness.COMMERCIAL,
    status=ClaimStatus.OPEN,
    loss_date=date(2026, 6, 8),
    reported_date=date(2026, 6, 8),
    insured=_INSURED,
    claimant=_CLAIMANT,
    additional_parties=[],
    loss_location=_LOSS_LOCATION,
    loss_cause="Rear-end collision — third party at fault (FL Statute 316.0895)",
    description=(
        "Rear-end collision at I-75 & Exit 42, Miami, FL. "
        "Insured vehicle (2023 Freightliner Cascadia, plate FL-LGT-8821) struck from behind "
        "by third-party vehicle while stopped at traffic signal. "
        "Minor injuries reported; driver M. Torres is ambulatory."
    ),
    total_incurred=MoneyAmount(amount=Decimal("8450.00"), currency="USD"),
    total_reserves=MoneyAmount(amount=Decimal("8450.00"), currency="USD"),
    total_payments=MoneyAmount(amount=Decimal("0.00"), currency="USD"),
    open_reserves=MoneyAmount(amount=Decimal("8450.00"), currency="USD"),
    litigation_flag=False,
    siu_flag=False,
    created_at=datetime(2026, 6, 8, 14, 32, 0),
    updated_at=datetime(2026, 6, 13, 10, 4, 12),
    assigned_adjuster_id="usr-john-smith",
    source_system=SourceSystem.CLAIMCENTER,
)

_NOTES = [
    ClaimNote(
        note_id="nte-001",
        claim_id=_CLAIM_ID,
        note_type=NoteType.GENERAL,
        subject="Initial Contact — Coverage Confirmed",
        body=(
            "Initial contact with insured. Confirmed coverage active. "
            "Vehicle towed to Riverside Auto Body."
        ),
        author_id="usr-john-smith",
        author_name="John Smith",
        created_at=datetime(2026, 6, 8, 16, 0, 0),
        ai_generated=False,
        source_system=SourceSystem.CLAIMCENTER,
    ),
    ClaimNote(
        note_id="nte-002",
        claim_id=_CLAIM_ID,
        note_type=NoteType.DAMAGES,
        subject="Repair Estimate Review — AI Assisted Draft",
        body=(
            "Reviewed repair estimate from Riverside Auto Body. Estimate: $6,200.00. "
            "Parts $3,800 / Labor $2,400. Consistent with photo evidence. "
            "Net insurer exposure after $2,500 deductible: $3,700.00. "
            "No frame damage identified."
        ),
        author_id="usr-john-smith",
        author_name="John Smith",
        created_at=datetime(2026, 6, 13, 10, 4, 10),
        ai_generated=True,
        approved_by="John Smith",
        source_system=SourceSystem.CLAIMCENTER,
    ),
]

_EXPOSURES = [
    ExposureSummary(
        exposure_id="exp-001",
        claim_id=_CLAIM_ID,
        coverage_type="Bodily Injury Liability",
        status=ExposureStatus.OPEN,
        claimant=_CLAIMANT,
        reserve=MoneyAmount(amount=Decimal("5000.00"), currency="USD"),
        payment=MoneyAmount(amount=Decimal("0.00"), currency="USD"),
        assigned_adjuster_id="usr-john-smith",
    ),
    ExposureSummary(
        exposure_id="exp-002",
        claim_id=_CLAIM_ID,
        coverage_type="Physical Damage — Collision",
        status=ExposureStatus.OPEN,
        claimant=_INSURED,
        reserve=MoneyAmount(amount=Decimal("3700.00"), currency="USD"),
        payment=MoneyAmount(amount=Decimal("0.00"), currency="USD"),
        assigned_adjuster_id="usr-john-smith",
    ),
    ExposureSummary(
        exposure_id="exp-003",
        claim_id=_CLAIM_ID,
        coverage_type="Rental Reimbursement",
        status=ExposureStatus.OPEN,
        claimant=_INSURED,
        reserve=MoneyAmount(amount=Decimal("750.00"), currency="USD"),
        payment=MoneyAmount(amount=Decimal("0.00"), currency="USD"),
        assigned_adjuster_id="usr-john-smith",
    ),
]

_ACTIVITIES = [
    ActivitySummary(
        activity_id="act-001",
        claim_id=_CLAIM_ID,
        activity_type=ActivityType.PHONE_CALL,
        subject="Initial contact — insured",
        description="Confirmed coverage. Authorized tow to Riverside Auto Body.",
        due_date=date(2026, 6, 8),
        completed_date=date(2026, 6, 8),
        assigned_to="usr-john-smith",
        created_at=datetime(2026, 6, 8, 14, 35, 0),
        completed=True,
    ),
    ActivitySummary(
        activity_id="act-002",
        claim_id=_CLAIM_ID,
        activity_type=ActivityType.INVESTIGATION,
        subject="Obtain medical records — M. Torres",
        description="Medical authorization request to be sent within 14 days.",
        due_date=date(2026, 6, 22),
        completed_date=None,
        assigned_to="usr-john-smith",
        created_at=datetime(2026, 6, 13, 10, 5, 0),
        completed=False,
    ),
    ActivitySummary(
        activity_id="act-003",
        claim_id=_CLAIM_ID,
        activity_type=ActivityType.INVESTIGATION,
        subject="Identify and contact third-party insurer",
        description="Subrogation potential — at-fault driver cited by police.",
        due_date=date(2026, 6, 20),
        completed_date=None,
        assigned_to="usr-john-smith",
        created_at=datetime(2026, 6, 13, 10, 5, 30),
        completed=False,
    ),
]

_RESERVES = [
    ReserveSummary(
        reserve_id="res-001",
        exposure_id="exp-001",
        claim_id=_CLAIM_ID,
        reserve_type=ReserveType.INDEMNITY,
        amount=MoneyAmount(amount=Decimal("5000.00"), currency="USD"),
        change_amount=MoneyAmount(amount=Decimal("5000.00"), currency="USD"),
        changed_at=datetime(2026, 6, 8, 16, 0, 0),
        changed_by="usr-john-smith",
    ),
    ReserveSummary(
        reserve_id="res-002",
        exposure_id="exp-002",
        claim_id=_CLAIM_ID,
        reserve_type=ReserveType.INDEMNITY,
        amount=MoneyAmount(amount=Decimal("3700.00"), currency="USD"),
        change_amount=MoneyAmount(amount=Decimal("3700.00"), currency="USD"),
        changed_at=datetime(2026, 6, 10, 12, 0, 0),
        changed_by="usr-john-smith",
    ),
    ReserveSummary(
        reserve_id="res-003",
        exposure_id="exp-003",
        claim_id=_CLAIM_ID,
        reserve_type=ReserveType.EXPENSE,
        amount=MoneyAmount(amount=Decimal("750.00"), currency="USD"),
        change_amount=MoneyAmount(amount=Decimal("750.00"), currency="USD"),
        changed_at=datetime(2026, 6, 9, 10, 0, 0),
        changed_by="usr-john-smith",
    ),
]

_PAYMENTS: list[PaymentSummary] = []  # No payments issued yet


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------


class MockClaimCenterProvider:
    """
    Specification-shaped mock implementation of ClaimCenter read and write
    interfaces.

    Returns Phase 1 claim data for CLM-2026-100245. Returns NOT_FOUND for
    all other claim IDs. Write methods always raise MockWriteDisabledError.

    NOTE — Specification alignment (ADR-004):
      When the real ClaimCenterReadAdapter is built against the Guidewire
      ClaimCenter REST API v10 specification, it will implement the same
      IClaimCenterReadProvider protocol. Field names from Guidewire's API
      (claimNumber, openDate, amountValue) are mapped to these models at
      the adapter boundary.
    """

    def __init__(self, sim: SimulationConfig | None = None) -> None:
        self._sim = sim or SimulationConfig()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> ProviderStatus:
        return ProviderStatus.MOCK

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    def get_claim(
        self,
        claim_id: str,
        context: ToolExecutionContext,
    ) -> GetClaimResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetClaimResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(
                    code="NOT_FOUND",
                    message=f"Claim '{claim_id}' not found in adjuster portfolio.",
                    source_system=SourceSystem.CLAIMCENTER,
                    retryable=False,
                ),
            )
        return GetClaimResult(status=ToolResultStatus.SUCCESS, claim=_CLAIM_DETAIL)

    def get_claims(
        self,
        adjuster_id: str,
        context: ToolExecutionContext,
        pagination: PaginationRequest | None = None,
        status_filter: list[ClaimStatus] | None = None,
    ) -> GetClaimsResult:
        apply_simulation(self._sim)
        all_claims = [_CLAIM_SUMMARY]
        if status_filter:
            all_claims = [c for c in all_claims if c.status in status_filter]
        items, page_meta = paginate(all_claims, pagination)
        return GetClaimsResult(
            status=ToolResultStatus.SUCCESS,
            claims=items,
            pagination=page_meta,
        )

    def get_claim_notes(
        self,
        claim_id: str,
        context: ToolExecutionContext,
        pagination: PaginationRequest | None = None,
        note_type_filter: list[NoteType] | None = None,
    ) -> GetClaimNotesResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetClaimNotesResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(code="NOT_FOUND", message=f"Claim '{claim_id}' not found.",
                                source_system=SourceSystem.CLAIMCENTER, retryable=False),
            )
        notes = _NOTES
        if note_type_filter:
            notes = [n for n in notes if n.note_type in note_type_filter]
        items, page_meta = paginate(notes, pagination)
        return GetClaimNotesResult(
            status=ToolResultStatus.SUCCESS, notes=items, pagination=page_meta
        )

    def get_exposures(
        self,
        claim_id: str,
        context: ToolExecutionContext,
    ) -> GetExposuresResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetExposuresResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(code="NOT_FOUND", message=f"Claim '{claim_id}' not found.",
                                source_system=SourceSystem.CLAIMCENTER, retryable=False),
            )
        return GetExposuresResult(status=ToolResultStatus.SUCCESS, exposures=_EXPOSURES)

    def get_activities(
        self,
        claim_id: str,
        context: ToolExecutionContext,
        pagination: PaginationRequest | None = None,
    ) -> GetActivitiesResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetActivitiesResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(code="NOT_FOUND", message=f"Claim '{claim_id}' not found.",
                                source_system=SourceSystem.CLAIMCENTER, retryable=False),
            )
        items, page_meta = paginate(_ACTIVITIES, pagination)
        return GetActivitiesResult(
            status=ToolResultStatus.SUCCESS, activities=items, pagination=page_meta
        )

    def get_reserves(
        self,
        claim_id: str,
        context: ToolExecutionContext,
    ) -> GetReservesResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetReservesResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(code="NOT_FOUND", message=f"Claim '{claim_id}' not found.",
                                source_system=SourceSystem.CLAIMCENTER, retryable=False),
            )
        return GetReservesResult(status=ToolResultStatus.SUCCESS, reserves=_RESERVES)

    def get_payments(
        self,
        claim_id: str,
        context: ToolExecutionContext,
        pagination: PaginationRequest | None = None,
    ) -> GetPaymentsResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetPaymentsResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(code="NOT_FOUND", message=f"Claim '{claim_id}' not found.",
                                source_system=SourceSystem.CLAIMCENTER, retryable=False),
            )
        items, page_meta = paginate(_PAYMENTS, pagination)
        return GetPaymentsResult(
            status=ToolResultStatus.SUCCESS, payments=items, pagination=page_meta
        )

    # ------------------------------------------------------------------
    # Write methods — DISABLED (ADR-002 Phase 2B)
    # ------------------------------------------------------------------

    def create_claim_note(
        self,
        request: CreateClaimNoteRequest,
        context: ToolExecutionContext,
    ) -> WriteOperationResult:
        """
        WRITE DISABLED — Phase 2B only (ADR-002).
        Always raises MockWriteDisabledError.
        """
        raise MockWriteDisabledError()

    def create_activity(
        self,
        request: CreateActivityRequest,
        context: ToolExecutionContext,
    ) -> WriteOperationResult:
        """
        WRITE DISABLED — Phase 2B only (ADR-002).
        Always raises MockWriteDisabledError.
        """
        raise MockWriteDisabledError()
