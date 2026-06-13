# domains/claims/models/

Claims domain model ownership and boundaries.

## Ownership

This directory owns the **business domain model** for insurance claims. It is the authoritative definition of what a claim means to this application — not what ClaimCenter stores, not what the API returns.

The shared contracts (`shared/contracts/`) define the cross-layer data shapes.
This directory defines the domain's internal representation, business rules, and invariants.

## Boundary Rules

| Allowed | Not Allowed |
|---------|-------------|
| Import from `shared/contracts/python/` | Import from `adapters/` |
| Import from `shared/schemas/` | Import from `backend/` |
| Define domain-specific value objects | Call external APIs or databases |
| Define business rules as pure functions | Use FastAPI, SQLAlchemy, or HTTP clients |
| Raise domain exceptions | Raise HTTP exceptions |

## What Belongs Here

- **Enriched domain models** — domain-layer representations that may carry more context than the wire contracts (e.g., computed risk scores, validated state machines)
- **Value objects** — immutable types with equality based on value, not identity (e.g., `ReserveAmount`, `JurisdictionCode`)
- **Domain exceptions** — `ClaimNotFoundError`, `InvalidClaimStateError`, `GovernanceViolationError`
- **Business rule functions** — `classify_risk_level(claim)`, `is_eligible_for_ai_summary(claim)`, `requires_supervisor_review(claim)`
- **Domain constants** — reserve thresholds, escalation triggers, supported claim types

## What Does Not Belong Here

- Database models or ORM decorators
- HTTP request/response schemas
- Adapter-specific data shapes
- Any I/O or external system calls

## Structure (to be built)

```
domains/claims/models/
├── __init__.py
├── claim_domain_model.py      # Enriched domain model with business rules
├── value_objects.py           # ReserveAmount, JurisdictionCode, RiskScore
├── exceptions.py              # ClaimNotFoundError, InvalidClaimStateError
└── risk_classifier.py         # classify_risk_level() — pure function
```

## Relationship to shared/contracts/python/

```
ClaimCenter API (adapter)
      │
      │ translates into
      ▼
shared/contracts/python/Claim     ← wire contract, minimal, stable
      │
      │ enriched into
      ▼
domains/claims/models/ClaimDomainModel  ← business model, richer, domain rules
      │
      │ used by
      ▼
domains/claims/use_cases/           ← application logic
```
