# shared/components/

Shared Python utilities with no layer dependencies.

## Responsibility

Pure utility functions and helpers used across multiple layers. Nothing here imports from `backend/`, `services/`, `adapters/`, or `domains/`. All functions are stateless and side-effect free.

## Contents (to be built)

```
shared/components/
├── id_generator.py       # UUID generation with domain prefixes (e.g. "claim_", "evt_")
├── datetime_utils.py     # UTC datetime helpers, ISO 8601 formatting
├── masking.py            # PII masking utilities for logs and audit output
├── pagination.py         # Shared pagination cursor logic
└── result.py             # Result/Either type for explicit error handling
```

## Design Constraints

- No imports from any other project layer
- No I/O, no network calls, no database access
- Functions are pure — same input always produces same output
- Fully unit-testable without mocking
