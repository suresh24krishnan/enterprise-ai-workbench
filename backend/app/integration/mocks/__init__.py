# backend/app/integration/mocks
#
# Specification-backed mock providers.
# Populated in Sprint 2 — one mock per enterprise provider contract.
#
# Mocks simulate real system behaviour: same field names, HTTP status codes,
# error shapes, and pagination as the real system (ADR-004).
# An integration test that passes against a mock must pass against the
# real provider without code changes.
