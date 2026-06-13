# adapters/claimcenter/

ClaimCenter adapter — implements claim data access and note writing.

## Responsibility

Provides the implementation of `IClaimRepository` and `IClaimNoteWriter` against Guidewire ClaimCenter (or mock in Phase 1).

## Interfaces Implemented

```python
class IClaimRepository(Protocol):
    def get_claim(self, claim_id: str) -> Claim | None: ...
    def search_claims(self, query: ClaimSearchQuery) -> list[ClaimSummary]: ...
    def get_claim_documents(self, claim_id: str) -> list[ClaimDocument]: ...

class IClaimNoteWriter(Protocol):
    def draft_note(self, claim_id: str, content: str) -> NoteDraft: ...
    def write_note(self, claim_id: str, note_id: str, approved_by: str) -> NoteWriteResult: ...
```

## Implementations

| File | Environment Value | Description |
|------|------------------|-------------|
| `mock_claim_repository.py` | `CLAIMCENTER_ADAPTER=mock` | Returns data from `mock-data/claims/` |
| `claimcenter_http_adapter.py` | `CLAIMCENTER_ADAPTER=sandbox` or `production` | Calls ClaimCenter REST API |

## Mock Behavior

The mock adapter:
- Reads claim data from `mock-data/claims/*.json`
- Simulates realistic claim structures including parties, coverages, notes, and documents
- Simulates write operations (notes are logged but not persisted to any real system)
- Returns deterministic responses for predictable testing

## Note Write Governance

Writing a note to ClaimCenter always requires:
1. An AI-drafted note reviewed by the user
2. Governance engine ALLOW decision (or human override of ESCALATE)
3. Explicit human approval action in the UI
4. Audit event recorded before and after the write
