# Phase 2A API Inventory

**Total endpoints:** 21 (excluding framework routes `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect`, `/health`)
**All endpoints:** Read-only except where noted
**Writes enabled:** Never in Phase 2A

---

## Health

| Method | Path      | Description             | Write? |
|--------|-----------|-------------------------|--------|
| GET    | `/health` | Application liveness check | No   |

**Response:**
```json
{ "status": "ok", "version": "0.1.0" }
```

---

## Session

| Method | Path          | Description            | Write? |
|--------|---------------|------------------------|--------|
| GET    | `/api/session`| Current user session   | No     |

---

## Claims (Phase 1)

| Method | Path                                | Description                        | Write?              |
|--------|-------------------------------------|------------------------------------|---------------------|
| GET    | `/api/claims`                       | List all claims                    | No                  |
| GET    | `/api/claims/{claim_id}`            | Get claim detail                   | No                  |
| GET    | `/api/claims/{claim_id}/summary`    | AI-generated claim summary         | No                  |
| GET    | `/api/claims/{claim_id}/evidence`   | Supporting evidence for claim      | No                  |
| GET    | `/api/claims/{claim_id}/conversation` | Conversation history             | No                  |
| POST   | `/api/claims/{claim_id}/conversation/turn` | Submit conversation turn  | Simulated (no persist)|
| GET    | `/api/claims/{claim_id}/draft-note` | Draft note for review              | No                  |
| GET    | `/api/claims/{claim_id}/approval`   | Approval record                    | No                  |
| POST   | `/api/claims/{claim_id}/approval`   | Submit approval (mock, no write)   | MockWriteDisabledError|
| GET    | `/api/claims/{claim_id}/audit`      | Audit timeline                     | No                  |

---

## Integration Status (Sprint 3)

| Method | Path                          | Description                         | Write? |
|--------|-------------------------------|-------------------------------------|--------|
| GET    | `/api/integration/status`     | Provider registry health + governance | No   |

**Response fields:**
- `global_mode` — always `"mock"` in Phase 2A
- `writes_enabled` — always `false`
- `lab_safe` — always `true`
- `validation` — `"PASS"` when all 6 adapters pass contract checks
- `providers[]` — per-provider status with mock/real indicator

---

## Supervisor (Sprint 5)

| Method | Path                              | Description                           | Write? |
|--------|-----------------------------------|---------------------------------------|--------|
| POST   | `/api/integration/supervisor/run` | Execute governed tool orchestration   | No     |

**Request body:**
```json
{ "claim_id": "CLM-2026-100245", "intent": "claim_summary" }
```

**Intent values:** `claim_summary` · `coverage_analysis` · `fraud_check` · `document_review` · `policy_lookup`

**Response fields:**
- `request_id` — UUID per execution
- `intent` — classified intent
- `selected_providers` — ordered provider list from planner
- `execution_trace[]` — per-provider: provider, method, status, latency_ms
- `aggregated_result` — merged provider data (no email body, no secrets)
- `status` — `success` | `partial` | `failed`
- `governance_flags` — writes_enabled, provider_mode_enforced, real_providers_rejected, etc.
- `latency_ms` — total wall-clock time

**Governance enforcement:** Pre-execution check. Any violation → HTTP 422. Zero providers execute.

---

## Control Tower (Sprint 6)

| Method | Path                                        | Description                          | Write? |
|--------|---------------------------------------------|--------------------------------------|--------|
| GET    | `/api/integration/control-tower/runs`       | Recent supervisor runs (newest first)| No     |
| GET    | `/api/integration/control-tower/runs/{id}`  | Full execution detail for a run      | No     |
| GET    | `/api/integration/control-tower/summary`    | Aggregate health summary             | No     |

**Store:** In-memory ring buffer, max 25 runs, cleared on restart.

**What is NOT stored:** aggregated_result, email body, document body, secrets, stack traces.

**Control Tower run fields:**
- `request_id`, `claim_id`, `intent`, `selected_providers`
- `steps[]` — provider, method, status, latency_ms, error_code, error_message
- `governance` — all 5 governance flags
- `status`, `latency_ms`, `provider_count`, `succeeded_count`, `failed_count`, `recorded_at`

---

## Evaluation (Sprint 7)

| Method | Path                                              | Description                          | Write? |
|--------|---------------------------------------------------|--------------------------------------|--------|
| GET    | `/api/integration/evaluation/scenarios`           | All 10 golden scenarios              | No     |
| POST   | `/api/integration/evaluation/run`                 | Run one scenario through supervisor  | No     |
| GET    | `/api/integration/evaluation/runs`                | Recent evaluation runs (newest first)| No     |
| GET    | `/api/integration/evaluation/report/{run_id}`     | Full evaluation result               | No     |
| GET    | `/api/integration/evaluation/report/{run_id}/recommendation` | Promotion recommendation | No  |
| GET    | `/api/integration/evaluation/summary`             | Aggregate evaluation health          | No     |

**Store:** In-memory ring buffer, max 50 results, cleared on restart.

**POST /run request body:**
```json
{ "scenario_id": "GS-001" }
```

**Evaluation result fields:**
- `run_id`, `scenario_id`, `scenario_name`, `claim_id`, `intent`
- `expectation` — the golden expectation
- `actual_providers`, `actual_success_count`, `actual_latency_ms`, etc.
- `score` — 6 weighted dimensions + overall_score (0–100)
- `regressions[]` — regression_type, severity, detail, expected, actual
- `status` — `pass` | `fail` | `error`
- `passed` — boolean (score >= 80 AND no critical regressions)
- `reason`, `recorded_at`

**Recommendation values:** `PROMOTE` | `BLOCK` | `REVIEW`

---

## API Summary Table

| Category          | GET | POST | Total |
|-------------------|-----|------|-------|
| Health/Session    | 2   | 0    | 2     |
| Claims (Phase 1)  | 8   | 2    | 10    |
| Integration Status| 1   | 0    | 1     |
| Supervisor        | 0   | 1    | 1     |
| Control Tower     | 3   | 0    | 3     |
| Evaluation        | 5   | 1    | 6     |
| Framework (docs)  | 4   | 0    | 4     |
| **Total**         | **23** | **4** | **27** |

No DELETE. No PUT. No PATCH. No authentication required (LAB environment).
