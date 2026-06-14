# Phase 2 Control Tower

**Sprint 6 — Control Tower Observability**
**Branch:** `phase-2-enterprise-integration-foundation`
**Status:** Active — in-memory trace store, 3 API endpoints, React UI page

---

## Purpose

The Control Tower is the observability layer for the Phase 2 supervisor.
It answers the question: "What exactly happened when the supervisor ran?"

Without observability:
- A supervisor execution is a black box — you know the final result but
  not which providers were called, in what order, how long each took,
  or what governance decisions were made.
- Demo audiences cannot see the governed orchestration in action.
- Debugging a partial failure requires log diving.
- Leadership cannot verify that writes are disabled and mock mode is enforced.

With the Control Tower:
- Every supervisor execution is captured as a structured ControlTowerRun.
- The UI shows recent runs, per-provider status and latency, and governance flags.
- A single click opens the full execution trace for any run.
- The summary endpoint provides aggregate health at a glance.

---

## Why observability matters

The supervisor is deterministic (Sprint 5). But "deterministic" is not the
same as "observable." A governance-controlled system needs to be auditable —
stakeholders need evidence that:

1. Only mock providers were used (no real Guidewire calls).
2. Writes were disabled on every execution.
3. Provider failures were caught and traced, not silently ignored.
4. Latency is within acceptable bounds.
5. The governance gate ran before any provider call.

The Control Tower provides that evidence in real time, without requiring
access to server logs.

---

## What is captured

Each ControlTowerRun stores:

```
request_id          — UUID identifying this execution
claim_id            — which claim was processed
intent              — e.g. "claim_summary", "fraud_check"
selected_providers  — ordered list of providers the planner chose
steps[]             — per-provider execution trace:
  provider          — provider name
  method            — method called (e.g. "get_claim")
  status            — success | not_found | error
  latency_ms        — time taken for this provider call
  retryable         — whether the error is retryable
  error_code        — error code if failed (e.g. "NOT_FOUND")
  error_message     — human-readable error (no secrets)
governance          — governance flags at execution time:
  writes_enabled              — always False in Phase 2A
  provider_mode_enforced      — always "mock" in Sprint 6
  real_providers_rejected     — always True
  all_operations_read_only    — always True
  phase_2b_gate_open          — always False
status              — overall: success | partial | failed
latency_ms          — total wall-clock time
provider_count      — number of providers in the plan
succeeded_count     — providers that returned success
failed_count        — providers that failed or errored
recorded_at         — ISO-8601 UTC timestamp
```

---

## What is intentionally NOT captured

The following are explicitly excluded from the trace store:

| Excluded | Reason |
|---|---|
| Claim document body text | UNTRUSTED DATA — ADR-006 |
| Email body text | UNTRUSTED DATA from external parties — ADR-006 |
| API tokens, credentials | Never stored anywhere in Phase 2A |
| Internal stack traces | Security / information disclosure |
| Raw provider response bodies | Unnecessary; metadata is sufficient |
| PII beyond claim_id | Minimal footprint |

The aggregated_result from the supervisor (which contains provider data) is
never stored in the Control Tower. Only the execution trace metadata is kept.

---

## Privacy and security restrictions

- The trace store is in-memory only. No data is written to disk.
- The store is cleared on process restart.
- No authentication is required for the Control Tower API in the LAB environment.
  Production deployment must add authentication before exposing these endpoints.
- No secrets, tokens, or credentials appear in any response.
- The email aggregator already excludes body text (ADR-006); the Control Tower
  adds a second layer by not storing aggregated_result at all.

---

## How this supports the leadership demo

The Control Tower page at `/control-tower` shows:

1. **Summary metrics** — total runs, success rate, average latency.
2. **Governance status panel** — six governance invariants confirmed green.
3. **Recent runs list** — click any row to open the full execution trace.
4. **Run detail modal** — per-provider step with method, status, latency,
   governance flags, and selected providers.

A demo flow:
1. Navigate to `/control-tower`.
2. POST to `/api/integration/supervisor/run` with `claim_id=CLM-2026-100245`
   and `intent=claim_summary`.
3. Click Refresh — the run appears in the list.
4. Click the row — the detail modal shows all 5 providers succeeded in <5ms each.
5. Governance panel shows: Writes Disabled ✓, Read-Only ✓, Real Rejected ✓.

This demonstrates governed, traceable, mock-safe orchestration to leadership
without requiring any real Guidewire connectivity.

---

## How this supports future Guidewire integration

When real adapters are registered (Phase 2B):

1. The trace store captures the same fields — only the provider name and
   latency change, not the schema.
2. The Control Tower will show real latency (e.g. 250ms for ClaimCenter
   instead of <1ms for the mock).
3. Governance flags will reflect when the Phase 2B write gate opens —
   `phase_2b_gate_open: true` will appear in the trace.
4. Partial failures from real adapters will surface as `status: partial`
   runs with `error_code` and `error_message` on the failed step.

The Control Tower is adapter-agnostic. It works the same for mock and real.

---

## API

```
GET /api/integration/control-tower/runs
    Returns: list[ControlTowerRunSummary] — newest first, max 25
    Fields: request_id, claim_id, intent, status, provider_count,
            succeeded_count, failed_count, latency_ms, writes_enabled,
            provider_mode, recorded_at

GET /api/integration/control-tower/runs/{request_id}
    Returns: ControlTowerRun — full detail
    Errors: 404 if not found (in-memory store cleared on restart)

GET /api/integration/control-tower/summary
    Returns: ControlTowerSummary
    Fields: total_runs, success_count, partial_count, failed_count,
            average_latency_ms, writes_enabled (false), lab_safe (true),
            provider_modes, store_capacity, store_used
```

---

## Future production evolution

### Persistent trace store

Replace `trace_store.py` with a PostgreSQL-backed store. The `service.py`
and API layers are unchanged — only the store implementation changes.

```python
# trace_store.py → persistent implementation
def record_run(run: ControlTowerRun) -> None:
    db.session.add(ControlTowerRunModel.from_domain(run))
    db.session.commit()
```

### OpenTelemetry

Emit each supervisor run as an OpenTelemetry span with per-provider child spans.
The Control Tower API becomes a complement to the OTEL dashboard, not a
replacement.

### SIEM integration

Forward ControlTowerRun events to Splunk, Datadog, or the enterprise SIEM
for security event correlation. The structured format (JSON, typed fields)
makes ingestion straightforward.

### Audit ledger integration

When Phase 2B write gate is satisfied, each supervisor run that triggers a
write is linked to an audit ledger entry. The Control Tower shows the
write-back outcome alongside the execution trace.

---

## Module structure

```
backend/app/integration/control_tower/
  __init__.py     — package description
  models.py       — ControlTowerRun, ControlTowerRunSummary,
                    ControlTowerGovernanceSummary, ControlTowerSummary
  trace_store.py  — in-memory ring buffer (25 entries, LAB only)
  service.py      — SupervisorResponse → ControlTowerRun conversion + queries

backend/app/api/
  routes_control_tower.py  — GET /api/integration/control-tower/runs
                              GET /api/integration/control-tower/runs/{id}
                              GET /api/integration/control-tower/summary

frontend/src/pages/
  ControlTowerPage.tsx     — /control-tower React page

frontend/src/App.tsx       — route added: /control-tower
frontend/src/components/layout/Sidebar.tsx  — nav item added
```

---

## Write gate status

Writes remain disabled. The Control Tower `governance.writes_enabled` field
is always `false`. It is a structural invariant set in `service.py`, not
derived from runtime configuration.
