# Phase 2 Supervisor Layer

**Sprint 5 — Supervisor & Tool Orchestration**
**Branch:** `phase-2-enterprise-integration-foundation`
**Status:** Active — deterministic orchestration over all 6 mock providers

---

## Why the supervisor is deterministic, not agentic

An agentic system decides at runtime which tools to call, in what order,
and with what inputs. That decision is made by an LLM and can differ
between runs for the same input.

The supervisor is not that.

For a given intent, the supervisor always selects the same providers,
calls the same methods, and follows the same aggregation rules. There is
no LLM in the orchestration pipeline. No randomness. No dynamic re-planning.
The only variable is the data returned by the mock providers — and that is
also deterministic (the mocks return fixed fixture data).

This matters because:
- Deterministic orchestration can be validated (Sprint 4 suite still passes).
- Deterministic orchestration can be governed (governance check is a hard gate).
- Deterministic orchestration produces reproducible audit trails.
- Deterministic orchestration does not require LLM trust for safety.

When real Guidewire providers replace the mocks, the orchestration logic is
unchanged. Only the data source changes, not the orchestration decisions.

---

## Execution lifecycle

```
SupervisorRequest
      │
      ▼
  [PLAN]
  classify_intent(raw_intent) → ClaimIntent
  build_plan(intent) → [provider_name, ...]
      │
      ▼
  [GOVERNANCE CHECK]
  enforce_governance(plan, registry)
  ├── writes_enabled must be False
  ├── all providers must resolve to MOCK mode
  └── REAL providers → raise IntegrationConfigError → HTTP 422
      │
      ▼
  [EXECUTE]
  For each provider in plan:
    provider = registry.resolve(provider_name)   ← registry only, never direct
    result = provider.<primary_read_method>(claim_id, ctx)
    trace = ProviderTrace(provider, method, status, latency_ms, error)
      │
      ▼
  [AGGREGATE]
  aggregate(intent, traces, raw_results)
  → {intent, providers: {name: {...}}}
  → SupervisorStatus (SUCCESS | PARTIAL | FAILED)
      │
      ▼
  SupervisorResponse
  ├── request_id
  ├── intent
  ├── selected_providers[]
  ├── execution_trace[]
  ├── aggregated_result{}
  ├── status
  ├── governance_flags{}
  └── latency_ms
```

---

## How the supervisor uses the registry

The supervisor never instantiates providers directly. Every provider
is obtained through `registry.resolve(provider_name)`.

This is a hard architectural rule, enforced by the executor:

```python
# CORRECT — registry is the sole source
provider = registry.resolve("claimcenter")

# WRONG — never do this
provider = MockClaimCenterProvider()
```

This rule ensures:
- Provider selection logic lives in one place (the registry + config).
- Swapping mock → real requires only a registry change, not an executor change.
- Governance mode checks apply consistently to all provider resolutions.
- The supervisor is oblivious to whether it is talking to a mock or a real adapter.

---

## Planner vs executor vs aggregator

### Planner (`planner.py`)

Answers: "Which providers do I need for this intent?"

Responsibilities:
- Classify raw intent string → `ClaimIntent` enum (rule-based, not ML).
- Return a static ordered list of provider names for each intent.

Does NOT:
- Call providers.
- Know how to call providers.
- Adapt the plan based on prior results.

```
claim_summary      → [claimcenter, policycenter, edw, fraud, email]
coverage_analysis  → [claimcenter, policycenter]
fraud_check        → [claimcenter, fraud]
document_review    → [documents]
policy_lookup      → [policycenter, edw]
```

### Executor (`executor.py`)

Answers: "How do I call each provider and what happened?"

Responsibilities:
- Resolve each provider from the registry.
- Call the provider's primary read method.
- Apply one mock-safe retry on retryable errors (timeout, unavailable).
- Record a `ProviderTrace` for every call regardless of outcome.
- Never propagate exceptions to the caller.

Does NOT:
- Choose which providers to call (that is the planner's job).
- Merge or interpret results (that is the aggregator's job).
- Call write methods.
- Instantiate providers directly.

### Aggregator (`aggregator.py`)

Answers: "What does the combined result mean?"

Responsibilities:
- Extract and normalise the meaningful fields from each provider's result.
- Produce a serialisable dict keyed by provider name.
- Determine overall `SupervisorStatus` (SUCCESS / PARTIAL / FAILED).
- Exclude untrusted content from the output (email body text — ADR-006).

Does NOT:
- Call providers.
- Retry failed results.
- Apply governance rules.

---

## Governance enforcement model

Governance is checked **before any provider call**. If governance fails,
zero providers are executed and `IntegrationConfigError` is raised.

```
enforce_governance(plan, registry)
├── Check 1: writes_enabled is structurally False (invariant)
└── Check 2: all providers in plan are MOCK mode
    ├── MOCK  → allowed
    ├── HYBRID → allowed (per-provider mode resolved; MOCK underneath)
    └── REAL  → IntegrationConfigError → HTTP 422, no execution
```

Sprint 5 restriction: REAL providers are always rejected. This is enforced
even if a real factory is registered — the supervisor governance layer is
a separate, explicit gate above the registry.

Phase 2B: when the write gate is opened, a new governance check will be
added here that verifies all 9 write-gate conditions before allowing any
write-capable intent through the supervisor.

---

## Untrusted content handling (ADR-006)

Email body text is UNTRUSTED DATA from external parties (claimants,
attorneys, vendors). The supervisor enforces ADR-006 in the aggregator:

- Email body text is **never included** in `aggregated_result`.
- Only email metadata is aggregated: subject, direction, sent_at,
  thread_id, from_party display name.
- This applies even in mock mode, so the isolation code is unchanged
  when real emails replace mock emails.

The aggregated result is safe to pass to the AI supervisor layer
(Phase 3) without additional isolation because body text is already excluded.

---

## Why this enables future Guidewire integration

When the real `RealClaimCenterAdapter` is registered in Phase 2B:

1. The governance layer checks it is in MOCK or approved HYBRID mode.
2. The executor resolves it from the registry (no code change in executor).
3. The executor calls `provider.get_claim(claim_id, ctx)` — the same
   method name as the mock.
4. The aggregator processes the result the same way — it only inspects
   standard contract fields (`claim.claim_id`, `claim.claim_status`, etc.).
5. The Sprint 4 validation suite certifies the real adapter implements
   the same contract before it is allowed into the registry.

The supervisor, executor, and aggregator are adapter-agnostic. Adapter
substitution is transparent to the orchestration layer.

---

## Observability

Every supervisor execution produces:

- `execution_trace[]` — per-provider: method, status, latency_ms, error
- `governance_flags{}` — writes_enabled, mode enforced, real_rejected
- `latency_ms` — total wall-clock time
- `succeeded_count` / `failed_count` — per-intent health signal

Structured logging is emitted at DEBUG (per-provider) and INFO (request
start/end). No secrets, tokens, or stack traces are logged.

---

## API

```
POST /api/integration/supervisor/run

Request:
{
  "claim_id": "CLM-2026-100245",
  "intent": "claim_summary",
  "context": {}
}

Response: SupervisorResponse
{
  "request_id": "...",
  "intent": "claim_summary",
  "selected_providers": ["claimcenter", "policycenter", "edw", "fraud", "email"],
  "execution_trace": [...],
  "aggregated_result": {
    "intent": "claim_summary",
    "providers": {
      "claimcenter": {"status": "success", "claim_id": "...", ...},
      "policycenter": {"status": "success", ...},
      ...
    }
  },
  "status": "success",
  "governance_flags": {
    "writes_enabled": false,
    "provider_mode_enforced": "mock",
    "real_providers_rejected": true,
    "all_operations_read_only": true,
    "phase_2b_gate_open": false
  },
  "latency_ms": 12.3,
  "provider_count": 5,
  "succeeded_count": 5,
  "failed_count": 0
}
```

Error responses:
- `422` — Governance violation (e.g. REAL provider configured).
- `500` — Unexpected supervisor error (see server logs).

---

## Module structure

```
backend/app/integration/supervisor/
  __init__.py      — package description
  models.py        — SupervisorRequest, SupervisorResponse, ProviderTrace,
                     GovernanceFlags, ClaimIntent, SupervisorStatus
  planner.py       — intent classification + provider plan lookup
  executor.py      — registry-backed provider call execution + tracing
  aggregator.py    — multi-provider result merging
  governance.py    — pre-execution constraint enforcement
  supervisor.py    — core orchestration engine (INPUT→PLAN→GOV→EXEC→AGG→RESP)

backend/app/api/
  routes_supervisor.py  — POST /api/integration/supervisor/run
```

---

## Write gate status

Writes remain disabled. The supervisor never sets `writes_enabled=True`.
The governance layer enforces this structurally. The Phase 2B write gate
(9-condition, ADR-002) has not been satisfied.
