# domains/

Business domain logic — the heart of the application.

## Responsibility

Contains domain models, business rules, and use cases for each business domain. Domain code is pure Python — it has no knowledge of HTTP, databases, AI providers, or any infrastructure. It depends only on interfaces.

## Domains

| Domain | Description |
|--------|-------------|
| `claims/` | Claims processing — the first and primary business domain |

## Design Constraints

- Domain code never imports from `adapters/` or `backend/`
- Domain code depends on interfaces (`IClaimRepository`, `IGovernanceEngine`, etc.) only
- Domain models (e.g., `Claim`, `ClaimNote`) are plain Python dataclasses or Pydantic models
- Business rules live here — not in services, not in the backend
- Domains are independently testable without any infrastructure

## Future Domains

The architecture supports adding additional business domains alongside Claims:

- `policies/` — policy management and coverage analysis
- `litigation/` — legal matter tracking
- `subrogation/` — recovery workflows

Each domain follows the same structure and dependency rules as `claims/`.
