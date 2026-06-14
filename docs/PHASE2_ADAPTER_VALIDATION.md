# Phase 2 Adapter Validation Suite

**Sprint 4 — Adapter Validation Suite**
**Branch:** `phase-2-enterprise-integration-foundation`
**Status:** Active — all 6 providers pass full validation suite

---

## Purpose

The adapter validation suite provides a deterministic certification layer
that every enterprise provider (mock today, real in future sprints) must
pass before it can serve production traffic.

It answers four questions per provider:

1. **Contract compliance**: does the provider implement all required methods?
2. **Schema validity**: do all method return values conform to the ToolResult
   standard format?
3. **Error normalization**: do failure paths return structured errors rather
   than raw exceptions?
4. **Failure mode support**: does the provider survive injected adverse
   conditions (timeout, unavailability, empty responses)?

No single broken provider can crash the suite. Each dimension runs
independently and failures are recorded, not propagated.

---

## Why validation precedes real adapters

Without a validation suite:
- A real adapter could implement 5 of 7 required methods and silently fail
  on the 6th.
- A real adapter could return raw `ValueError` instead of `ToolError` on a
  bad Guidewire response, crashing the AI supervisor.
- A real adapter could accept a write call silently instead of raising
  `MockWriteDisabledError`, bypassing the Phase 2B write gate.
- Schema drift between mock and real would not be caught until a live
  adjuster saw a crash.

With the validation suite:
- Every required method is checked at integration time, not at runtime.
- Every result shape is verified structurally — `status`, `error`, and
  `pagination` fields must all be correct.
- Every error path must normalize to `ToolError` (not raw exceptions).
- Every write path must raise `MockWriteDisabledError` (or the Phase 2B
  equivalent) — no silent writes.
- When a real adapter is registered, it runs the same suite automatically.
  If it fails, the CI pipeline fails. No silent regressions.

---

## Contract enforcement model

The contract spec is defined in `contract_validator.py`:

```python
_REQUIRED_METHODS = {
    "claimcenter": [
        "health", "get_claim", "get_claims", "get_claim_notes",
        "get_exposures", "get_activities", "get_reserves", "get_payments",
        "create_claim_note",  # write stub — must exist, must raise MockWriteDisabledError
        "create_activity",
    ],
    "email": [
        "health", "get_claim_correspondence", "get_email_thread", "draft_email",
        # send_email is in _FORBIDDEN_METHODS — must NOT exist
    ],
    ...
}

_FORBIDDEN_METHODS = {
    "email": ["send_email"],
}
```

Validation is **structural and behavioral**:
- Structural: method exists and is callable (no API calls made)
- Behavioral (response/error/injection dimensions): method is called with
  fixture data and the result shape is checked

---

## Validation dimensions

### 1. Contract validation (`contract_validator.py`)

Purely structural. Inspects the provider instance without calling methods.

- Checks method presence and callability for all required methods
- Checks absence of forbidden methods (e.g. `send_email`)
- Returns `ContractValidationResult` with per-violation detail

### 2. Response validation (`response_validator.py`)

Calls provider read methods against known fixture data:
- Claim: `CLM-2026-100245` (known) + `UNKNOWN-99999` (unknown)
- Policy: `CA-2024-8812`
- Customer: `EDW-CUST-10042`
- Documents: `doc-001` through `doc-005`

Checks per result:
- `status` is a `ToolResultStatus` value
- `SUCCESS` results have no `error` field set
- `NOT_FOUND`/`ERROR` results have a fully-populated `ToolError`
  (`code`, `message`, `source_system`, `retryable`)
- Paginated results have a valid `PaginationResponse`
  (`page >= 1`, `page_size >= 1`, `total_records >= 0`, `has_next` bool)

### 3. Error normalization (`error_validator.py`)

Validates that all error paths produce normalized, structured errors:

- **Write gate** (ClaimCenter only): `create_claim_note` and `create_activity`
  must raise `MockWriteDisabledError` with a Phase 2B message
- **Failure modes**: for each of 6 failure modes (NOT_FOUND, UNAUTHORIZED,
  FORBIDDEN, RATE_LIMITED, TIMEOUT, UNAVAILABLE), the provider must raise
  the correct `MockIntegrationError` subclass with the correct `retryable` flag
- **send_email absence**: `email` provider must not have a `send_email` method

### 4. Failure injection (`failure_injection.py`)

Simulates adverse conditions against the provider boundary:

| Scenario | What is tested |
|---|---|
| Timeout injection | Provider raises `MockTimeoutError(retryable=True)` |
| Unavailability injection | Provider raises `MockUnavailableError(retryable=True)` |
| Empty response (unknown ID) | Provider returns `NOT_FOUND` with error — does not raise |
| Partial response (out-of-range page) | Provider returns `SUCCESS` with empty list — does not crash |
| fail_after_n=2 | Provider succeeds twice then fails on 3rd call |
| Rapid successive calls (×5) | Provider handles 5 calls without state corruption |

---

## Failure injection strategy

Failure injection uses `SimulationConfig` to configure the provider's
behavior without modifying any application state:

```python
# Inject timeout into claimcenter
sim = SimulationConfig(failure_mode=FailureMode.TIMEOUT)
provider = MockClaimCenterProvider(sim=sim)
provider.get_claim("CLM-2026-100245", ctx)  # → raises MockTimeoutError

# Inject fail_after_n for retry testing
sim = SimulationConfig(failure_mode=FailureMode.TIMEOUT, fail_after_n=2)
provider = MockClaimCenterProvider(sim=sim)
provider.get_claim(...)  # call 1 → success
provider.get_claim(...)  # call 2 → success
provider.get_claim(...)  # call 3 → MockTimeoutError
```

This is safe because:
- Each test instantiates a new provider with its own `SimulationConfig`
- No shared state between test runs
- No enterprise calls at any point
- The default provider (no sim config) is unaffected

---

## How this protects future Guidewire integration

When the real `RealClaimCenterAdapter` is registered (Phase 2B+):

1. The contract validator checks all 10 required methods are implemented.
2. The response validator calls the real adapter against the lower Guidewire
   environment and verifies the result shapes match the contract models.
3. The error validator verifies that `401 Unauthorized` from Guidewire maps
   to `MockUnauthorizedError` (or its real equivalent) with `retryable=False`,
   not a raw `requests.exceptions.HTTPError`.
4. The failure validator tests that the adapter raises the correct exception
   types under simulated latency and dependency failures.

The suite is the **contract between the mock and the real adapter**.
An adapter that passes the suite is certified to be substitutable for the mock
in the registry without any changes to the AI supervisor or the tool layer.

---

## How this ensures deterministic behavior

The mock providers return the same data on every call. The validation suite
exploits this:
- Known IDs always return the same fixture data
- Unknown IDs always return NOT_FOUND
- Paginated results always have the same total_records

This means the validation suite is deterministic — it produces the same
pass/fail result on every run, making it suitable for CI/CD gating.

When real adapters are tested, determinism requires a stable test fixture
in the lower Guidewire environment. The validation suite validates the
adapter shape; integration tests validate the business data.

---

## Run modes

| Mode | What runs | Side effects |
|---|---|---|
| `DRY_RUN` | Contract + wiring checks only | None — no method calls |
| `FULL` | All four dimensions | Calls mock provider methods with fixture data |

The `GET /api/integration/status` endpoint runs a `DRY_RUN` on first
call to populate the `last_validation` summary. No method calls are
made from the status endpoint.

---

## Module structure

```
backend/app/integration/validation/
  __init__.py            — package description
  contract_validator.py  — structural interface compliance
  response_validator.py  — output shape and pagination correctness
  error_validator.py     — error normalization and write gate
  failure_injection.py   — adverse condition simulation
  runner.py              — orchestration and report generation
```

---

## Status endpoint integration

`GET /api/integration/status` now includes:

```json
{
  "last_validation": {
    "run_mode": "dry_run",
    "run_at": "2026-06-13T10:00:00+00:00",
    "total_providers": 6,
    "passed": 6,
    "failed": 0,
    "overall_status": "PASS"
  }
}
```

**What is NOT exposed:**
- Individual provider violation details
- Stack traces
- Internal exception messages
- Method-level failure reasons

The endpoint exposes aggregate counts only. Detailed results are available
through the runner API for authorized operational use.

---

## Write gate status

Writes remain disabled. The error validator confirms this by calling
`create_claim_note` and `create_activity` and verifying they raise
`MockWriteDisabledError` with a Phase 2B gate message.

The 9-condition write gate (ADR-002) has not been satisfied.
