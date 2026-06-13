# shared/

Shared resources used across multiple layers of the application.

## Responsibility

Contains artifacts that are referenced by more than one of: backend, services, domains, or adapters. Shared resources have no dependencies on any layer — they are pure data or pure utility.

## Contents

| Directory | Description |
|-----------|-------------|
| `schemas/` | Shared Pydantic schemas and TypeScript types for cross-layer data contracts |
| `prompts/` | Versioned AI prompt templates used by the orchestration and domain services |
| `policies/` | Governance policy definitions (YAML/JSON) read by the governance engine |
| `components/` | Shared Python utilities with no layer dependencies |

## Design Constraints

- `shared/` has no imports from `backend/`, `services/`, `adapters/`, or `domains/`
- Schemas here are the single source of truth for cross-layer data shapes
- Prompts are versioned — changing a prompt is a tracked change
- Policies are data, not code — operators can update policies without redeployment
- Utilities in `components/` are pure functions with no side effects
