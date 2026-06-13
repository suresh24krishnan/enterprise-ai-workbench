# services/audit/

Audit service — immutable record of every significant event in the system.

## Responsibility

Records every event that matters for compliance, debugging, and explainability. The audit trail is append-only and immutable — records are never updated or deleted.

## Interface: `IAuditStore`

```python
class IAuditStore(Protocol):
    def record(self, event: AuditEvent) -> str: ...              # returns event_id
    def query(self, filters: AuditQuery) -> list[AuditEvent]: ...
    def get_event(self, event_id: str) -> AuditEvent | None: ...
```

## Audited Event Types

| Event | When |
|-------|------|
| `user.login` | User authenticates |
| `user.logout` | User session ends |
| `claim.selected` | User opens a claim |
| `ai.summary.generated` | AI produces a claim summary |
| `ai.qa.turn` | A conversation turn with AI |
| `ai.note.drafted` | AI drafts a ClaimCenter note |
| `governance.evaluated` | Governance engine makes a decision |
| `human.approval.requested` | Escalation presented to human |
| `human.approval.granted` | Human approves an AI action |
| `human.approval.denied` | Human rejects an AI action |
| `claimcenter.note.written` | Note written back to ClaimCenter |
| `rag.retrieval` | Knowledge retrieved for AI context |

## Audit Event Schema

Every event includes:

- `event_id` — unique identifier
- `event_type` — from the list above
- `timestamp` — UTC ISO 8601
- `user_id` — who triggered the action
- `session_id` — current session
- `claim_id` — related claim (if applicable)
- `payload` — event-specific data
- `governance_decision` — ALLOW / DENY / ESCALATE (if applicable)

## Phase Evolution

| Phase | Backend |
|-------|---------|
| 1 | SQLite (local) |
| 2+ | Splunk / Elastic / enterprise audit platform |

The `IAuditStore` interface is identical across phases — only the adapter changes.
