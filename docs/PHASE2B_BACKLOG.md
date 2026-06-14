# Phase 2B Backlog

**Status:** Planned — not started
**Prerequisite:** Phase 2A frozen and all 10 golden scenarios PASS (confirmed)
**Branch:** `phase-2b-real-provider-integration` (to be created)

---

## Entry Criteria

Before Phase 2B work begins, all of the following must be satisfied:

| Criterion | Status |
|---|---|
| All 10 golden scenarios PASS on Phase 2A branch | SATISFIED |
| Sprint 4–7 validation suites: 0 failures | SATISFIED |
| Completion report reviewed by stakeholders | PENDING |
| Legal/compliance review of data handling | PENDING |
| Guidewire sandbox credentials obtained | PENDING |
| Phase 2B adapter factory implemented | PENDING |
| `phase_2b_gate_open` flag change approved | PENDING |

---

## Phase 2B Work Items

### P2B-001 — Real ClaimCenter Adapter

**Priority:** P0
**Description:** Implement `RealClaimCenterProvider` that calls the Guidewire
ClaimCenter REST API. Must satisfy the same `ClaimCenterProvider` protocol
as the mock.

**Acceptance criteria:**
- GS-001, GS-002, GS-003, GS-006, GS-007, GS-008, GS-009 all PASS against real adapter
- Latency under 500ms (evaluation `max_latency_ms` threshold)
- No secrets in aggregated_result or Control Tower trace
- ADR-006 email body exclusion still enforced

**Implementation notes:**
- Register factory in `bootstrap.py` under `ProviderMode.REAL`
- Set `phase_2b_gate_open = True` in governance after approval
- New golden scenarios GS-101+ covering real-provider responses

---

### P2B-002 — Real PolicyCenter Adapter

**Priority:** P0
**Description:** Implement `RealPolicyCenterProvider` against Guidewire
PolicyCenter REST API.

**Acceptance criteria:**
- GS-002, GS-005, GS-008 PASS against real adapter
- Coverage details include real deductible, limits, coverage types

---

### P2B-003 — Real EDW Adapter

**Priority:** P1
**Description:** Implement `RealEDWProvider` against the enterprise data
warehouse API or JDBC connection.

**Acceptance criteria:**
- GS-005, GS-006, GS-007 PASS with real customer profile data
- `CustomerProfile.years_as_customer` reflects real tenure

---

### P2B-004 — Real Fraud Adapter

**Priority:** P1
**Description:** Implement `RealFraudProvider` against the Fraud Detection
microservice (internal REST or gRPC).

**Acceptance criteria:**
- GS-003, GS-009 PASS
- `FraudAssessment.risk_score` is real model output
- SIU recommendation reflects actual fraud signals

---

### P2B-005 — Real Email Adapter

**Priority:** P1
**Description:** Implement `RealEmailProvider` against Microsoft Graph API
or the claims inbox microservice.

**Critical constraint:** ADR-006 MUST be enforced. The adapter implementation
must NEVER include email body text in `EmailMessage`. Only metadata fields are
permitted. This must be enforced at the adapter layer, not the aggregator.

**Acceptance criteria:**
- GS-001, GS-006, GS-007 PASS
- Email body never appears in aggregated_result or Control Tower trace
- Subject line only — no body

---

### P2B-006 — Write Gate

**Priority:** P2
**Description:** Open the Phase 2B write gate to enable `create_claim_note`
and `create_activity` under governed conditions.

**Prerequisite:** Explicit approval workflow (ApprovalPage) completed,
legal review passed, audit trail confirmed.

**What changes:**
- `MockWriteDisabledError` replaced by real write implementation in ClaimCenter adapter
- `GovernanceFlags.writes_enabled` set to `True` for approved write flows only
- `phase_2b_gate_open` set to `True` in governance
- Idempotency keys enforced on all write calls

**What does NOT change:**
- Read-only flows remain read-only
- ADR-006 email body exclusion remains in force
- Control Tower still captures only trace metadata

---

### P2B-007 — Hybrid Mode Support

**Priority:** P2
**Description:** Support `ProviderMode.HYBRID` — some providers real, some mock.
Useful for incremental rollout (real ClaimCenter, mock everything else).

**Implementation:** `ProviderRegistry.resolve()` already supports HYBRID mode.
No orchestration changes needed. Governance must log per-provider mode in trace.

---

### P2B-008 — Persistent Control Tower Store

**Priority:** P3
**Description:** Replace the in-memory `deque` trace store with a PostgreSQL-
backed store. The `service.py` and API layers are unchanged.

```python
# trace_store.py → persistent
def record_run(run: ControlTowerRun) -> None:
    db.session.add(ControlTowerRunModel.from_domain(run))
    db.session.commit()
```

---

### P2B-009 — Authentication & Authorization

**Priority:** P1 (required before production)
**Description:** Add JWT-based authentication to all `/api/integration/*`
endpoints. Control Tower and Evaluation should require the `adjuster` or
`supervisor` role.

---

### P2B-010 — OpenTelemetry Integration

**Priority:** P3
**Description:** Emit each supervisor run as an OpenTelemetry span with
per-provider child spans. Control Tower becomes a supplement to the OTEL
dashboard, not a replacement.

---

### P2B-011 — Golden Dataset Expansion

**Priority:** P0 (must precede real provider go-live)
**Description:** Add golden scenarios GS-101 through GS-110 covering:
- Real ClaimCenter responses (not_found behavior for unknown claims)
- Real latency bounds (> 50ms, < 500ms)
- Real fraud score distributions
- Hybrid mode (real claimcenter + mock everything else)

---

### P2B-012 — SIEM Integration

**Priority:** P3
**Description:** Forward `ControlTowerRun` events to Splunk or Datadog.
The structured JSON format makes ingestion straightforward.

---

## What Does NOT Change in Phase 2B

The following Phase 2A components are frozen and must not be modified
without a new ADR:

- Supervisor execution model (plan → govern → execute → aggregate)
- Contract interfaces (adding fields is OK; removing is not)
- Governance pre-execution enforcement
- ADR-006 email body exclusion
- Evaluation scoring weights and pass threshold
- Control Tower trace metadata model

---

## Phase 2B Success Criteria

Phase 2B is complete when:

1. All P2B-001 through P2B-006 work items delivered
2. Real adapter golden scenarios (GS-101+) PASS at >= 90/100
3. Write gate opened under governance with full audit trail
4. Authentication enforced on all integration endpoints
5. Persistent trace store deployed and verified
6. End-to-end demo with real Guidewire sandbox passes
7. Compliance sign-off obtained

---

## Timeline (Indicative)

| Milestone                        | Target    |
|----------------------------------|-----------|
| Phase 2A freeze (this document)  | 2026-06-14|
| Guidewire sandbox access         | TBD       |
| P2B-001 ClaimCenter adapter      | TBD       |
| P2B-005 Email adapter (ADR-006)  | TBD       |
| P2B-006 Write gate               | TBD       |
| P2B-009 Authentication           | TBD       |
| Phase 2B complete                | TBD       |
