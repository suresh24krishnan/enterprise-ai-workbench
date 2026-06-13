"""
Dependency injection wiring.

This is the only place in the backend that imports concrete adapter/repository
implementations. All other code depends on the IClaimRepository interface.

To swap implementations (e.g. Phase 1 mock → Phase 2 ClaimCenter):
  1. Create a new repository class that implements IClaimRepository.
  2. Update the factory function below to return the new implementation.
  3. Change nothing else.
"""

from typing import Protocol

from backend.app.config import get_settings
from backend.app.repositories.mock_claim_repository import MockClaimRepository
from backend.app.services.claim_service import ClaimService
from backend.app.services.conversation_service import ConversationService


class IClaimRepository(Protocol):
    """
    Interface contract for claim data access.
    The service layer depends only on this — never on a concrete class.
    """

    def list_claims(self) -> list:
        ...

    def get_claim(self, claim_id: str) -> dict | None:
        ...

    def get_claim_summary(self, claim_id: str) -> dict | None:
        ...

    def get_claim_evidence(self, claim_id: str) -> list | None:
        ...

    def get_claim_audit(self, claim_id: str) -> list | None:
        ...


def _build_claim_repository() -> IClaimRepository:
    """
    Factory: selects the correct repository based on environment config.
    Phase 1: mock
    Phase 2+: add ClaimCenterRepository here, select by CLAIMCENTER_ADAPTER env var.
    """
    settings = get_settings()
    if settings.claimcenter_adapter == "mock":
        return MockClaimRepository()
    # Future: elif settings.claimcenter_adapter == "sandbox": return ClaimCenterRepository(...)
    raise ValueError(f"Unknown CLAIMCENTER_ADAPTER: {settings.claimcenter_adapter}")


def get_claim_service() -> ClaimService:
    """FastAPI dependency: returns a fully wired ClaimService."""
    repo = _build_claim_repository()
    return ClaimService(repo)


def get_conversation_service() -> ConversationService:
    """FastAPI dependency: returns a fully wired ConversationService."""
    repo = _build_claim_repository()
    return ConversationService(repo)
