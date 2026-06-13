# shared/contracts/

Stable cross-layer data contracts — the single source of truth for all shared data shapes.

## What Contracts Are

A contract is a versioned, typed definition of a data structure that crosses a layer boundary. Contracts are:

- **Stable** — changes are deliberate and versioned, not incidental
- **Canonical** — every layer uses these definitions; no layer defines its own copy
- **Typed** — Python uses Pydantic; TypeScript uses interfaces with enums
- **Simple** — only the fields that cross boundaries; no internal implementation state

## What Contracts Are Not

- They are not database models (no ORM annotations)
- They are not HTTP request/response bodies (no FastAPI route metadata)
- They are not component props (no React-specific concerns)
- They are not internal service state (no processing or intermediate fields)

## Structure

```
shared/contracts/
├── README.md                    # This file
├── typescript/                  # TypeScript interfaces for the frontend
│   ├── claim.ts
│   ├── claimSummary.ts
│   ├── evidenceSource.ts
│   ├── conversationTurn.ts
│   ├── draftClaimNote.ts
│   ├── governanceDecision.ts
│   ├── auditEvent.ts
│   └── modelRouteDecision.ts
└── python/                      # Pydantic models for the backend and services
    ├── claim.py
    ├── claim_summary.py
    ├── evidence_source.py
    ├── conversation_turn.py
    ├── draft_claim_note.py
    ├── governance_decision.py
    ├── audit_event.py
    └── model_route_decision.py
```

## Versioning Policy

- Contracts are versioned by adding a `_v2` suffix to the filename when breaking changes are required
- Additive changes (new optional fields) do not require a new version
- Removing or renaming a field always requires a new version
- Both versions are supported during a transition period, then the old version is deleted

## Cross-Language Consistency

The TypeScript and Python contracts define the same concepts. Field names use:
- `camelCase` in TypeScript (language convention)
- `snake_case` in Python (language convention)

The underlying data shapes and enum values are identical.
