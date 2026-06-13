"""
Conversation endpoints for the claim-scoped AI assistant.

GET  /api/claims/{claim_id}/conversation        — fetch conversation history
POST /api/claims/{claim_id}/conversation/turn   — submit a user turn and get an AI response
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.dependencies import get_conversation_service
from backend.app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/claims", tags=["conversation"])


class TurnRequest(BaseModel):
    user_message: str
    session_id: str


@router.get("/{claim_id}/conversation")
def get_conversation(
    claim_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    result = service.get_conversation(claim_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return result


@router.post("/{claim_id}/conversation/turn")
def post_conversation_turn(
    claim_id: str,
    body: TurnRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    if not body.user_message.strip():
        raise HTTPException(status_code=422, detail="user_message must not be empty.")
    result = service.add_turn(claim_id, body.user_message.strip(), body.session_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")
    return result
