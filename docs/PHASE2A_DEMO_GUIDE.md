# Phase 2A Leadership Demo Guide

**Audience:** Engineering leadership, enterprise architects, product stakeholders
**Duration:** 15–20 minutes
**Environment:** LAB (HF Lab Space or local `uvicorn` + Vite dev server)
**Prerequisites:** Backend running on port 8000, frontend on port 5173

---

## Demo Objective

Demonstrate that the Enterprise AI Workbench has a governed, traceable,
mock-safe orchestration platform ready for real provider integration.
The audience should leave knowing:

1. The system knows which providers to call for each intent — without an LLM
2. Every execution is governed — writes blocked, real providers blocked
3. Every execution is observable — Control Tower shows the full trace
4. Every execution is measurable — evaluation gives a 0–100 quality score
5. The system is ready for Phase 2B — real Guidewire adapter integration

---

## Setup (5 minutes before demo)

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev

# Browser
open http://localhost:5173
```

Verify:
- `/health` returns `{"status":"ok"}`
- `/api/integration/status` shows `global_mode=mock writes_enabled=false lab_safe=true validation=PASS`

---

## Section 1 — Governed Orchestration (5 min)

**What to say:** "When a claim handler asks about a claim, the supervisor decides
which enterprise systems to query — deterministically, with governance enforced
before any provider is called."

**Step 1.1** — Open `http://localhost:5173/control-tower`

Show the empty Control Tower (no runs yet).
Point out: **Writes Disabled** · **Mock Mode** badges in the header.

**Step 1.2** — POST a supervisor run (use browser, curl, or the API docs at `/docs`):

```bash
curl -s -X POST http://localhost:8000/api/integration/supervisor/run \
  -H "Content-Type: application/json" \
  -d '{"claim_id":"CLM-2026-100245","intent":"claim_summary"}' | python -m json.tool
```

**What to show in the response:**
- `status: "success"` — all providers succeeded
- `selected_providers: ["claimcenter","policycenter","edw","fraud","email"]` — 5 providers
- `governance_flags.writes_enabled: false` — governance enforced
- `governance_flags.real_providers_rejected: true` — only mock providers used
- `latency_ms: <5` — sub-millisecond mock execution

**What to say:** "Notice the response is 5 providers — the planner chose exactly
the right set for a claim summary without calling an LLM to decide."

---

## Section 2 — Control Tower Observability (5 min)

**Step 2.1** — Refresh `http://localhost:5173/control-tower`

Show the run appearing in **Recent Supervisor Runs**.
Point out the status badge (SUCCESS), provider count (5/5), latency.

**Step 2.2** — Click the run row to open the **Execution Explorer**

Walk through each section top to bottom:

| Section | What to point out |
|---|---|
| Claim Summary | Request ID, intent, execution time, provider count |
| Execution Badges | READ ONLY · MOCK · NO WRITES · LAB SAFE · 5/5 PROVIDERS |
| Provider Health | Five green cards — ClaimCenter, PolicyCenter, EDW, Fraud, Email |
| Execution Timeline | Supervisor Started → each provider → Aggregation Complete → Governance Verified → Response Returned |
| Governance | Five checkmarks + expandable "Why this execution was allowed" |
| Execution Trace | Per-provider method(), status, latency |

**Step 2.3** — Click "Why this execution was allowed"

Read the 5 reasons aloud:
- Mock providers only — no Guidewire connectivity
- Writes disabled — all operations are read-only
- No external connectivity — Phase 2B gate closed
- Phase 2A policy satisfied
- Governance checks passed

**What to say:** "A governance violation — like requesting a real provider or
enabling writes — raises HTTP 422 before any provider call is made."

---

## Section 3 — Evaluation Quality Gate (5 min)

**Step 3.1** — Run a golden scenario:

```bash
curl -s -X POST http://localhost:8000/api/integration/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"GS-001"}' | python -m json.tool
```

**What to show:**
- `score.overall_score: 100.0` — perfect score
- `passed: true`
- `regressions: []` — zero deviations from golden expectation
- `score.provider_selection.reason: "Correct providers: ['claimcenter', 'edw', 'email', 'fraud', 'policycenter']"`
- `score.governance.reason: "Mock mode enforced, writes disabled"`

**Step 3.2** — Get the promotion recommendation:

```bash
curl -s http://localhost:8000/api/integration/evaluation/report/{run_id}/recommendation
```

Show: `"PROMOTE — All quality gates satisfied. Safe for Phase 2B promotion."`

**Step 3.3** — Show the summary:

```bash
curl -s http://localhost:8000/api/integration/evaluation/summary
```

Show: `pass_rate: 1.0`, `average_score: 100.0`, `regression_count: 0`

---

## Section 4 — Different Intents (3 min, optional)

Run two more intents to show deterministic routing:

```bash
# Fraud check — 2 providers only
curl -s -X POST http://localhost:8000/api/integration/supervisor/run \
  -H "Content-Type: application/json" \
  -d '{"claim_id":"CLM-2026-100245","intent":"fraud_check"}'

# Policy lookup — 2 different providers
curl -s -X POST http://localhost:8000/api/integration/supervisor/run \
  -H "Content-Type: application/json" \
  -d '{"claim_id":"CLM-2026-100245","intent":"policy_lookup"}'
```

**What to say:** "The planner maps intent to providers deterministically.
Fraud check always calls ClaimCenter and Fraud. Policy lookup always calls
PolicyCenter and EDW. No LLM involved in routing."

---

## Anticipated Questions

**Q: Why not use an LLM to decide which providers to call?**
A: Deterministic routing is auditable, testable, and fast. An LLM routing
layer would make the system non-deterministic — the same intent could route
to different providers on different runs. For a governed enterprise system,
that's unacceptable.

**Q: When do real Guidewire providers connect?**
A: Phase 2B. The adapter interface is already defined (contracts). We replace
the mock factory with a real Guidewire factory. The orchestration layer,
governance, and evaluation framework don't change.

**Q: How do we know a Guidewire adapter is correct?**
A: The evaluation framework runs the same 10 golden scenarios against the
real adapter. If it scores >= 80/100 and has no critical regressions, it's
promoted. The quality gate is the same regardless of adapter type.

**Q: What stops a developer from enabling writes?**
A: `MockWriteDisabledError` is raised at the adapter layer before any write
method executes. It cannot be bypassed without changing the contract
implementation. The governance layer also checks `writes_enabled=False`
before any provider call. Two independent enforcement layers.

**Q: Is the email body visible in the trace?**
A: No. ADR-006 (Untrusted Content Isolation) prohibits email body text from
appearing in the aggregated result or Control Tower trace. Only metadata is
captured: email_id, direction, subject, from_party, sent_at, thread_id.

---

## Demo Checklist

- [ ] Backend on port 8000 (all 21 routes responding)
- [ ] Frontend on port 5173 (Control Tower accessible)
- [ ] `/api/integration/status` shows `validation=PASS`
- [ ] Control Tower page loads (even if empty — shows governance badges)
- [ ] Supervisor run succeeds (5/5 providers, writes_enabled=false)
- [ ] Control Tower shows the run after Refresh
- [ ] Execution Explorer opens on click
- [ ] Governance Explainer expands
- [ ] Evaluation GS-001 scores 100.0
- [ ] Recommendation shows PROMOTE
