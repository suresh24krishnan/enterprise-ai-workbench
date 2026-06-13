"""
ConversationService — orchestrates claim-scoped assistant conversations.

Delegates data access to the repository; all mock AI logic lives in the
mock repository. Real implementations swap the repository only.
"""

from __future__ import annotations


class ConversationService:
    def __init__(self, repository) -> None:
        self._repo = repository

    def get_conversation(self, claim_id: str) -> dict | None:
        return self._repo.get_conversation(claim_id)

    def add_turn(self, claim_id: str, user_message: str, session_id: str) -> dict | None:
        return self._repo.add_conversation_turn(claim_id, user_message, session_id)
