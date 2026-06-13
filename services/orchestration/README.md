# services/orchestration/

Orchestration service — coordinates multi-step AI workflows.

## Responsibility

Manages complex, multi-turn AI interactions that require coordinating multiple services (model router, governance, RAG, audit) in the correct sequence. Maintains conversation state and enforces the governed workflow contract.

## Interface: `IConversationService`

```python
class IConversationService(Protocol):
    def start_conversation(self, claim_id: str, user_id: str) -> Conversation: ...
    def add_turn(self, conversation_id: str, user_message: str) -> ConversationTurn: ...
    def get_conversation(self, conversation_id: str) -> Conversation | None: ...
    def close_conversation(self, conversation_id: str) -> None: ...
```

## Governed Conversation Turn Sequence

For every user message:

```
1. Validate conversation is active
2. Record turn start to audit
3. Retrieve relevant knowledge (RAG)
4. Select model (Model Router)
5. Evaluate governance (Governance Engine)
   ├── DENY  ──▶ return denial, no model call
   ├── ESCALATE ──▶ pend turn, await human approval
   └── ALLOW ──▶ continue
6. Build governed prompt (message + knowledge chunks + system policy)
7. Call model (via IModelProvider)
8. Record full turn to audit (prompt, response, model, governance decision)
9. Return response to caller
```

## Conversation State

```python
class Conversation:
    conversation_id: str
    claim_id: str
    user_id: str
    status: Literal["active", "pending_approval", "closed"]
    turns: list[ConversationTurn]
    created_at: datetime
    updated_at: datetime
```

## Design Constraints

- Orchestration never calls models directly — always through `IModelRouter` + `IModelProvider`
- Governance is called on every turn — there are no exempt turns
- Conversation state is persisted — sessions survive backend restarts
- Human approval decisions are recorded in conversation state and in the audit store
