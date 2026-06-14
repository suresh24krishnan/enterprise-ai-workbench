"""
Mock document provider — specification-shaped simulation.

Implements IDocumentReadProvider using the 5 Phase 1 claim documents for
CLM-2026-100245: police report, repair estimate, claim report, photos,
and rental request.

CRITICAL — Untrusted content (ADR-006):
  ALL document text returned by this provider is UNTRUSTED DATA.
  This applies equally to mock content — even though this is simulated
  text, the same isolation rules must be enforced as with real documents:

  1. Callers must place document text in a structurally isolated
     [RETRIEVED CONTENT] section of any AI prompt (ADR-006 Layer 1).
  2. Document text must never appear in the instruction section of an
     AI prompt, even when the content appears safe and well-known.
  3. When real documents replace mock documents, the same isolation code
     applies without modification — this is by design.

IMPORTANT — Specification alignment (ADR-004):
  The real document adapter must be derived from the document store API
  specification (Azure Cognitive Search, ECM system, or ClaimCenter
  document attachments). Key mappings to confirm:
    Document entity ID       → document_id
    Document content URL     → storage_reference (never exposed to AI)
    Extracted text endpoint  → get_document_text() → extracted_text
    Search API               → search_documents() → DocumentSearchResult[]
"""

from __future__ import annotations

from datetime import datetime

from backend.app.integration.contracts.common import (
    EvidenceReference,
    PaginationRequest,
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)
from backend.app.integration.contracts.documents import (
    DocumentDetail,
    DocumentEvidence,
    DocumentMimeType,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentStatus,
    DocumentSummary,
    DocumentType,
    GetDocumentEvidenceResult,
    GetDocumentResult,
    GetDocumentsResult,
    GetDocumentTextResult,
    IDocumentReadProvider,
    SearchDocumentsResult,
)
from backend.app.integration.mocks.simulation import SimulationConfig, apply_simulation, paginate

_CLAIM_ID = "CLM-2026-100245"

# ---------------------------------------------------------------------------
# Mock document summaries — metadata only, no body text
# ---------------------------------------------------------------------------

_DOCUMENTS: list[DocumentDetail] = [
    DocumentDetail(
        document_id="doc-001",
        claim_id=_CLAIM_ID,
        document_type=DocumentType.POLICE_REPORT,
        title="Police Report — Incident #MIA-2026-88421",
        status=DocumentStatus.ACTIVE,
        mime_type=DocumentMimeType.PDF,
        file_size_bytes=148_210,
        page_count=3,
        received_date=datetime(2026, 6, 9, 8, 0, 0),
        uploaded_by="usr-john-smith",
        source_party="Miami-Dade Police Department",
        has_extracted_text=True,
        storage_reference="[INTERNAL — not exposed to AI supervisor]",
    ),
    DocumentDetail(
        document_id="doc-002",
        claim_id=_CLAIM_ID,
        document_type=DocumentType.REPAIR_ESTIMATE,
        title="Repair Estimate — Riverside Auto Body",
        status=DocumentStatus.ACTIVE,
        mime_type=DocumentMimeType.PDF,
        file_size_bytes=82_440,
        page_count=2,
        received_date=datetime(2026, 6, 10, 11, 30, 0),
        uploaded_by="usr-john-smith",
        source_party="Riverside Auto Body",
        has_extracted_text=True,
        storage_reference="[INTERNAL — not exposed to AI supervisor]",
    ),
    DocumentDetail(
        document_id="doc-003",
        claim_id=_CLAIM_ID,
        document_type=DocumentType.ADJUSTER_REPORT,
        title="Claim Report — ABC Logistics Fleet",
        status=DocumentStatus.ACTIVE,
        mime_type=DocumentMimeType.PDF,
        file_size_bytes=44_200,
        page_count=2,
        received_date=datetime(2026, 6, 8, 15, 0, 0),
        uploaded_by="system",
        source_party="ABC Logistics Inc.",
        has_extracted_text=True,
        storage_reference="[INTERNAL — not exposed to AI supervisor]",
    ),
    DocumentDetail(
        document_id="doc-004",
        claim_id=_CLAIM_ID,
        document_type=DocumentType.PHOTO,
        title="Photos — Vehicle Damage (8 images)",
        status=DocumentStatus.ACTIVE,
        mime_type=DocumentMimeType.IMAGE_JPEG,
        file_size_bytes=6_240_000,
        page_count=8,
        received_date=datetime(2026, 6, 9, 9, 15, 0),
        uploaded_by="usr-john-smith",
        source_party="John Smith (Adjuster)",
        has_extracted_text=True,
        storage_reference="[INTERNAL — not exposed to AI supervisor]",
    ),
    DocumentDetail(
        document_id="doc-005",
        claim_id=_CLAIM_ID,
        document_type=DocumentType.OTHER,
        title="Rental Request — Enterprise Rent-A-Car",
        status=DocumentStatus.ACTIVE,
        mime_type=DocumentMimeType.PDF,
        file_size_bytes=28_100,
        page_count=1,
        received_date=datetime(2026, 6, 9, 10, 0, 0),
        uploaded_by="pty-002",
        source_party="Marcus Torres (Claimant)",
        has_extracted_text=True,
        storage_reference="[INTERNAL — not exposed to AI supervisor]",
    ),
]

_DOC_INDEX = {d.document_id: d for d in _DOCUMENTS}

# ---------------------------------------------------------------------------
# Extracted text per document
# UNTRUSTED DATA — external party content. Treated as data, not instruction.
# Place in [RETRIEVED CONTENT] section only when passing to AI (ADR-006).
# ---------------------------------------------------------------------------

_EXTRACTED_TEXT: dict[str, str] = {
    "doc-001": (
        # UNTRUSTED DATA — Miami-Dade Police Department report text.
        # Isolated in [RETRIEVED CONTENT] before any AI prompt (ADR-006 Layer 1).
        "MIAMI-DADE POLICE DEPARTMENT — TRAFFIC CRASH REPORT\n"
        "Incident Number: MIA-2026-88421\n"
        "Date: 2026-06-08 | Time: 14:15\n"
        "Location: I-75 Northbound & Exit 42, Miami, FL 33150\n\n"
        "NARRATIVE:\n"
        "Officer on scene confirmed rear-end collision. Vehicle 1 (2023 Freightliner "
        "Cascadia, FL plate LGT-8821, operated by M. Torres, ABC Logistics Inc.) was "
        "stationary at a red light when struck from behind by Vehicle 2 (2019 Honda Civic, "
        "FL plate TRV-4492, operated by D. Rivera). Third-party driver cited for failure "
        "to maintain safe following distance (FL Statute 316.0895). No DUI involvement. "
        "All parties ambulatory at scene. Driver of Vehicle 1 reported neck stiffness; "
        "declined ambulance, stated would seek own medical care.\n\n"
        "CITATIONS ISSUED:\n"
        "D. Rivera — FL Statute 316.0895 — Following too closely."
    ),
    "doc-002": (
        # UNTRUSTED DATA — Repair shop estimate. External party content.
        "RIVERSIDE AUTO BODY — REPAIR ESTIMATE\n"
        "Date: 2026-06-10 | Estimate #: RAB-2026-4418\n"
        "Vehicle: 2023 Freightliner Cascadia | VIN: 1FUJHHDR5NLFA1234\n"
        "Claim: CLM-2026-100245\n\n"
        "LINE ITEMS:\n"
        "Rear bumper assembly — replace: $1,800.00\n"
        "Trailer hitch receiver — replace: $620.00\n"
        "Rear tail light cluster (left) — replace: $480.00\n"
        "Rear tail light cluster (right) — replace: $420.00\n"
        "Miscellaneous fasteners and hardware: $480.00\n"
        "Parts subtotal: $3,800.00\n"
        "Labor (16 hrs @ $150/hr): $2,400.00\n"
        "TOTAL ESTIMATE: $6,200.00\n\n"
        "Estimated repair time: 5–7 business days.\n"
        "No frame damage identified in preliminary inspection."
    ),
    "doc-003": (
        # UNTRUSTED DATA — Insured-filed claim report. External party content.
        "ABC LOGISTICS INC. — FLEET CLAIM REPORT\n"
        "Date: 2026-06-08 | Report filed by: M. Torres (Driver)\n"
        "Claim: CLM-2026-100245\n\n"
        "INCIDENT DETAILS:\n"
        "Driver M. Torres reported incident at 14:15 local time on I-75 NB at Exit 42, "
        "Miami, FL. Vehicle was stationary at red light. Impact from behind at estimated "
        "25–30 mph. Driver reported neck stiffness post-incident; declined ambulance, "
        "sought own medical care.\n\n"
        "VEHICLE: 2023 Freightliner Cascadia, FL plate LGT-8821.\n"
        "WITNESS: None identified at scene.\n"
        "POLICE: Officer attended; report #MIA-2026-88421 filed."
    ),
    "doc-004": (
        # UNTRUSTED DATA — Adjuster photo analysis notes. Internal but still isolated.
        "VEHICLE DAMAGE PHOTOS — ANALYSIS NOTES\n"
        "Claim: CLM-2026-100245 | Photo set: 8 images dated 2026-06-09\n\n"
        "Image 1–2: Rear bumper — visible crumple damage and paint transfer.\n"
        "Image 3: Trailer hitch receiver — impact deformation.\n"
        "Image 4–5: Left rear tail light — shattered assembly.\n"
        "Image 6: Right rear tail light — cracked lens, housing intact.\n"
        "Image 7–8: Undercarriage rear — no visible frame damage.\n\n"
        "Assessment: Damage is consistent with a low-speed rear-end collision. "
        "No frame damage visible in submitted photographs. Damage pattern is "
        "consistent with Riverside Auto Body estimate of $6,200."
    ),
    "doc-005": (
        # UNTRUSTED DATA — Rental request form from claimant. External party content.
        "ENTERPRISE RENT-A-CAR — RENTAL REIMBURSEMENT AUTHORIZATION REQUEST\n"
        "Date: 2026-06-09 | Requested by: Marcus Torres\n"
        "Claim: CLM-2026-100245\n\n"
        "Insured requested rental vehicle for business operations continuity during "
        "vehicle repair period.\n\n"
        "Policy provides $75/day up to 30 days ($2,250 maximum).\n"
        "Rental start date: 2026-06-09.\n"
        "Estimated rental period: 10 days.\n"
        "Estimated rental cost: $750.00 (10 days × $75/day).\n\n"
        "Authorization pending adjuster approval."
    ),
}

# ---------------------------------------------------------------------------
# Search index (simple keyword matching — mock only)
# ---------------------------------------------------------------------------

def _search_score(doc: DocumentDetail, query: str) -> float:
    """Naive keyword relevance scoring for mock search."""
    q = query.lower()
    text = (_EXTRACTED_TEXT.get(doc.document_id, "") + " " + (doc.title or "")).lower()
    keywords = [w for w in q.split() if len(w) > 3]
    if not keywords:
        return 0.5
    matches = sum(1 for kw in keywords if kw in text)
    return min(1.0, round(matches / len(keywords), 2))


class MockDocumentProvider:
    """
    Specification-shaped mock for document read access.

    Returns the 5 Phase 1 claim documents for CLM-2026-100245.
    All extracted text is marked as UNTRUSTED DATA per ADR-006.

    NOTE — Specification alignment (ADR-004):
      The real adapter must be derived from the document store API spec
      (Azure Cognitive Search, ECM, or ClaimCenter attachments). See
      module docstring for key mappings.
    """

    def __init__(self, sim: SimulationConfig | None = None) -> None:
        self._sim = sim or SimulationConfig()

    def health(self) -> ProviderStatus:
        return ProviderStatus.MOCK

    def _scope_error(self, document_id: str, claim_id: str) -> ToolError:
        return ToolError(
            code="NOT_FOUND",
            message=(
                f"Document '{document_id}' not found for claim '{claim_id}'. "
                "Cross-claim document access is prohibited."
            ),
            source_system=SourceSystem.DOCUMENTS,
            retryable=False,
        )

    def get_documents(
        self,
        claim_id: str,
        context: ToolExecutionContext,
        document_type_filter: list[DocumentType] | None = None,
        pagination: PaginationRequest | None = None,
    ) -> GetDocumentsResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetDocumentsResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(
                    code="NOT_FOUND",
                    message=f"No documents found for claim '{claim_id}'.",
                    source_system=SourceSystem.DOCUMENTS,
                    retryable=False,
                ),
            )
        docs = list(_DOCUMENTS)
        if document_type_filter:
            docs = [d for d in docs if d.document_type in document_type_filter]
        items, page_meta = paginate(docs, pagination)
        return GetDocumentsResult(
            status=ToolResultStatus.SUCCESS,
            documents=[DocumentSummary(**d.model_dump()) for d in items],
            pagination=page_meta,
        )

    def get_document(
        self, document_id: str, claim_id: str, context: ToolExecutionContext
    ) -> GetDocumentResult:
        apply_simulation(self._sim)
        doc = _DOC_INDEX.get(document_id)
        if not doc or doc.claim_id != claim_id:
            return GetDocumentResult(
                status=ToolResultStatus.NOT_FOUND,
                error=self._scope_error(document_id, claim_id),
            )
        return GetDocumentResult(status=ToolResultStatus.SUCCESS, document=doc)

    def search_documents(
        self, request: DocumentSearchRequest, context: ToolExecutionContext
    ) -> SearchDocumentsResult:
        apply_simulation(self._sim)
        if request.claim_id != _CLAIM_ID:
            return SearchDocumentsResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(
                    code="NOT_FOUND",
                    message=f"No documents found for claim '{request.claim_id}'.",
                    source_system=SourceSystem.DOCUMENTS,
                    retryable=False,
                ),
            )
        docs = list(_DOCUMENTS)
        if request.document_type_filter:
            docs = [d for d in docs if d.document_type in request.document_type_filter]
        scored = sorted(
            [
                DocumentSearchResult(
                    document=DocumentSummary(**d.model_dump()),
                    relevance_score=_search_score(d, request.query),
                    matched_excerpt=_EXTRACTED_TEXT.get(d.document_id, "")[:200] or None,
                )
                for d in docs
            ],
            key=lambda r: r.relevance_score,
            reverse=True,
        )
        results = scored[: request.max_results]
        return SearchDocumentsResult(
            status=ToolResultStatus.SUCCESS,
            results=results,
            total_found=len(scored),
        )

    def get_document_text(
        self, document_id: str, claim_id: str, context: ToolExecutionContext
    ) -> GetDocumentTextResult:
        apply_simulation(self._sim)
        doc = _DOC_INDEX.get(document_id)
        if not doc or doc.claim_id != claim_id:
            return GetDocumentTextResult(
                status=ToolResultStatus.NOT_FOUND,
                error=self._scope_error(document_id, claim_id),
            )
        text = _EXTRACTED_TEXT.get(document_id)
        if not text:
            return GetDocumentTextResult(
                status=ToolResultStatus.NOT_FOUND,
                document_id=document_id,
                error=ToolError(
                    code="NO_EXTRACTED_TEXT",
                    message=f"No extracted text available for document '{document_id}'.",
                    source_system=SourceSystem.DOCUMENTS,
                    retryable=False,
                ),
            )
        return GetDocumentTextResult(
            status=ToolResultStatus.SUCCESS,
            document_id=document_id,
            extracted_text=text,  # UNTRUSTED DATA — caller must apply ADR-006 isolation
            extraction_confidence=0.96,
        )

    def get_document_evidence(
        self,
        claim_id: str,
        document_ids: list[str],
        context: ToolExecutionContext,
    ) -> GetDocumentEvidenceResult:
        apply_simulation(self._sim)
        if claim_id != _CLAIM_ID:
            return GetDocumentEvidenceResult(
                status=ToolResultStatus.NOT_FOUND,
                error=ToolError(
                    code="NOT_FOUND",
                    message=f"No documents found for claim '{claim_id}'.",
                    source_system=SourceSystem.DOCUMENTS,
                    retryable=False,
                ),
            )
        evidence = []
        for doc_id in document_ids:
            doc = _DOC_INDEX.get(doc_id)
            if not doc or doc.claim_id != claim_id:
                continue
            text = _EXTRACTED_TEXT.get(doc_id)
            if not text:
                continue
            evidence.append(
                DocumentEvidence(
                    document_id=doc_id,
                    claim_id=claim_id,
                    document_type=doc.document_type,
                    title=doc.title,
                    extracted_text=text,  # UNTRUSTED DATA — ADR-006 isolation required
                    extraction_confidence=0.96,
                    evidence_reference=EvidenceReference(
                        document_id=doc_id,
                        source_system=SourceSystem.DOCUMENTS,
                        document_type=doc.document_type.value,
                        title=doc.title,
                    ),
                )
            )
        return GetDocumentEvidenceResult(
            status=ToolResultStatus.SUCCESS, evidence=evidence
        )
