"""
Claims API routes.
Routes delegate to ClaimService — no business logic here.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.dependencies import get_claim_service
from backend.app.services.claim_service import ClaimService

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.get("")
def list_claims(service: ClaimService = Depends(get_claim_service)):
    """Return a paginated list of claims for the current user."""
    return service.list_claims()


@router.get("/{claim_id}")
def get_claim(claim_id: str, service: ClaimService = Depends(get_claim_service)):
    """Return the full detail of a single claim."""
    claim = service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return claim


@router.get("/{claim_id}/summary")
def get_claim_summary(claim_id: str, service: ClaimService = Depends(get_claim_service)):
    """
    Return the governed AI-generated summary for a claim.
    Includes governance decision, model routing decision, and evidence sources.
    """
    summary = service.get_claim_summary(claim_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return summary


@router.get("/{claim_id}/evidence")
def get_claim_evidence(claim_id: str, service: ClaimService = Depends(get_claim_service)):
    """Return the evidence sources retrieved for the claim summary."""
    evidence = service.get_claim_evidence(claim_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return evidence


@router.get("/{claim_id}/audit")
def get_claim_audit(claim_id: str, service: ClaimService = Depends(get_claim_service)):
    """Return the audit trail for this claim session."""
    audit = service.get_claim_audit(claim_id)
    if audit is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return audit


@router.get("/{claim_id}/draft-note")
def get_draft_note(claim_id: str, service: ClaimService = Depends(get_claim_service)):
    """Return the AI-generated draft adjuster note for a claim."""
    note = service.get_draft_note(claim_id)
    if note is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return note


@router.get("/{claim_id}/approval")
def get_approval(claim_id: str, service: ClaimService = Depends(get_claim_service)):
    """Return the current approval state for a claim's draft note."""
    result = service.get_approval(claim_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return result


class ApprovalRequest(BaseModel):
    decision: str          # APPROVED | REJECTED | REVISION_REQUESTED
    reviewer_comments: str = ""
    reviewer_id: str = "usr-john-smith"
    reviewer_name: str = "John Smith"


@router.post("/{claim_id}/approval")
def submit_approval(
    claim_id: str,
    body: ApprovalRequest,
    service: ClaimService = Depends(get_claim_service),
):
    """Submit an approval decision for a claim's AI draft note."""
    allowed = {"APPROVED", "REJECTED", "REVISION_REQUESTED"}
    if body.decision not in allowed:
        raise HTTPException(status_code=422, detail=f"decision must be one of {allowed}")
    decided_at = datetime.now(timezone.utc).isoformat()
    result = service.submit_approval(
        claim_id,
        body.decision,
        body.reviewer_comments,
        body.reviewer_id,
        body.reviewer_name,
        decided_at,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return result
