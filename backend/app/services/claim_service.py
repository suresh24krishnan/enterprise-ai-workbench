"""
ClaimService — orchestrates claim-related operations.

The service layer:
  - Has no knowledge of HTTP (no Request, Response, or status codes)
  - Has no knowledge of which repository implementation is in use
  - Owns any data transformation or business logic between route and repository
"""

from __future__ import annotations


class ClaimService:
    def __init__(self, repository) -> None:
        self._repo = repository

    def list_claims(self) -> list:
        return self._repo.list_claims()

    def get_claim(self, claim_id: str) -> dict | None:
        return self._repo.get_claim(claim_id)

    def get_claim_summary(self, claim_id: str) -> dict | None:
        return self._repo.get_claim_summary(claim_id)

    def get_claim_evidence(self, claim_id: str) -> list | None:
        return self._repo.get_claim_evidence(claim_id)

    def get_claim_audit(self, claim_id: str) -> list | None:
        return self._repo.get_claim_audit(claim_id)

    def get_draft_note(self, claim_id: str) -> dict | None:
        return self._repo.get_draft_note(claim_id)

    def get_approval(self, claim_id: str) -> dict | None:
        return self._repo.get_approval(claim_id)

    def submit_approval(
        self,
        claim_id: str,
        decision: str,
        reviewer_comments: str,
        reviewer_id: str,
        reviewer_name: str,
        decided_at: str,
    ) -> dict | None:
        return self._repo.submit_approval(
            claim_id, decision, reviewer_comments, reviewer_id, reviewer_name, decided_at
        )
