# adapters/auditstore/

Audit store adapter — persists the immutable audit trail.

## Responsibility

Implements `IAuditStore` against the configured storage backend. In Phase 1 this is a local SQLite database. In Phase 2+ it integrates with enterprise audit platforms.

## Interface Implemented

```python
class IAuditStore(Protocol):
    def record(self, event: AuditEvent) -> str: ...
    def query(self, filters: AuditQuery) -> list[AuditEvent]: ...
    def get_event(self, event_id: str) -> AuditEvent | None: ...
```

## Implementations

| File | Environment Value | Description |
|------|------------------|-------------|
| `sqlite_audit_store.py` | `AUDIT_STORE=sqlite` | SQLite — local development |
| `splunk_audit_store.py` | `AUDIT_STORE=splunk` | Splunk HEC |
| `elastic_audit_store.py` | `AUDIT_STORE=elastic` | Elasticsearch |

## Immutability Contract

- Audit records are never updated or deleted
- The `record()` method is append-only
- SQLite implementation uses a write-only connection for the audit table
- Enterprise implementations use platform-native immutability features

## Audit Record Schema

```python
class AuditEvent:
    event_id: str          # UUID
    event_type: str        # e.g. "ai.summary.generated"
    timestamp: datetime    # UTC
    user_id: str
    session_id: str
    claim_id: str | None
    payload: dict          # event-specific data
    governance_decision: str | None   # ALLOW / DENY / ESCALATE
    model_id: str | None
    latency_ms: int | None
```
