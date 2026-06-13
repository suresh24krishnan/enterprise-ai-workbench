# docs/

Architecture documentation, API contracts, decision records, and runbooks.

## Responsibility

The authoritative reference for understanding the system's design, the decisions made, and how to operate it.

## Structure (to be built)

```
docs/
├── architecture/
│   ├── overview.md                   # System architecture narrative
│   ├── governed-ai-workflow.md       # Detailed AI workflow with governance
│   ├── hexagonal-architecture.md     # Ports and adapters pattern explanation
│   └── phase-evolution.md            # How the system evolves across phases
├── decisions/
│   ├── ADR-001-hexagonal-architecture.md
│   ├── ADR-002-sqlite-for-mvp.md
│   ├── ADR-003-governance-before-model-call.md
│   └── ADR-004-human-approval-for-writes.md
├── api/
│   └── openapi.yaml                  # OpenAPI spec (generated from FastAPI)
└── runbooks/
    ├── local-development.md          # How to run the system locally
    ├── adding-a-new-adapter.md       # How to add a new adapter implementation
    └── adding-a-new-domain.md        # How to add a new business domain
```

## Architecture Decision Records (ADRs)

ADRs document the significant decisions made during design and development. Each ADR records:
- The context and problem being solved
- The options considered
- The decision made and why
- The consequences of the decision

This ensures future contributors understand not just what was built, but why.

## Key Documents to Read First

1. `architecture/overview.md` — start here for system understanding
2. `architecture/governed-ai-workflow.md` — understand the governance contract
3. `runbooks/local-development.md` — get the system running locally
4. `runbooks/adding-a-new-adapter.md` — how to replace a Phase 1 mock
