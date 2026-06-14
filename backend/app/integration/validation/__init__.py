# backend/app/integration/validation
#
# Sprint 4 — Adapter Validation Suite
#
# Deterministic validation layer that certifies enterprise providers
# against shared contract standards.
#
# Modules:
#   contract_validator.py   — interface compliance (method existence + signatures)
#   response_validator.py   — output shape consistency and pagination correctness
#   error_validator.py      — error normalization compliance
#   failure_injection.py    — failure mode simulation and boundary testing
#   runner.py               — orchestration, structured report generation
#
# No business logic. No external calls. MOCK mode only.
# Validation runs against registered providers only.
