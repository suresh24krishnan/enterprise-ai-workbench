"""
Session endpoints.
In Phase 1: returns a mock session for any request.
In Phase 2+: validates a real JWT issued by the identity provider.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["session"])


class MockUser(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    permissions: list[str]


class SessionResponse(BaseModel):
    session_id: str
    user: MockUser
    identity_provider: str
    expires_at: str


@router.get("/session", response_model=SessionResponse)
def get_session() -> SessionResponse:
    """
    Returns the current session context.
    Phase 1: hardcoded mock adjuster session.
    Phase 2+: decode JWT from Authorization header and return real user.
    """
    return SessionResponse(
        session_id="sess-mock-001",
        user=MockUser(
            user_id="usr-john-smith",
            name="John Smith",
            email="john.smith@workbench.local",
            role="ADJUSTER",
            permissions=[
                "claims:read",
                "ai:generate",
                "notes:approve",
            ],
        ),
        identity_provider="mock",
        expires_at="2026-06-13T23:59:59Z",
    )
