# Phase 2A Module Inventory

**Backend modules:** 62 Python files
**Frontend pages:** 11 React pages + layout components
**Docs:** 9 architecture documents

---

## Backend — API Layer (`backend/app/api/`)

| Module                     | Sprint | Description                                          |
|----------------------------|--------|------------------------------------------------------|
| `routes_health.py`         | 1      | GET /health — application liveness                   |
| `routes_session.py`        | 1      | GET /api/session — user session                      |
| `routes_claims.py`         | 1      | Phase 1 claims endpoints (10 routes)                 |
| `routes_conversation.py`   | 1      | Conversation turn handling                           |
| `routes_integration.py`    | 3      | GET /api/integration/status                          |
| `routes_supervisor.py`     | 5      | POST /api/integration/supervisor/run + CT recording  |
| `routes_control_tower.py`  | 6      | 3 Control Tower GET endpoints                        |
| `routes_evaluation.py`     | 7      | 6 Evaluation endpoints                               |

---

## Backend — Integration Contracts (`backend/app/integration/contracts/`)

All contracts are read-only in Phase 2A. Write methods raise `MockWriteDisabledError`.

| Module              | Provider    | Key Read Methods                                      |
|---------------------|-------------|-------------------------------------------------------|
| `common.py`         | All         | `ToolExecutionContext`, `ProviderMode`, base classes  |
| `claimcenter.py`    | ClaimCenter | `get_claim()`, `get_claim_financials()`, `get_activity_log()` |
| `policycenter.py`   | PolicyCenter| `get_policy()`, `get_coverage_details()`             |
| `edw.py`            | EDW         | `get_customer_profile()`, `get_claim_history()`      |
| `fraud.py`          | Fraud       | `get_fraud_indicators()`                             |
| `email.py`          | Email       | `get_claim_correspondence()` (body excluded per ADR-006) |
| `documents.py`      | Documents   | `get_claim_documents()`                              |

---

## Backend — Mock Providers (`backend/app/integration/mocks/`)

| Module              | Provider    | Returns for CLM-2026-100245 |
|---------------------|-------------|------------------------------|
| `claimcenter.py`    | ClaimCenter | `ClaimDetail` — status, description, claimant, financials |
| `policycenter.py`   | PolicyCenter| `PolicySummary` — status, carrier, program, coverage    |
| `edw.py`            | EDW         | `CustomerProfile` — tenure, claims count, policy count  |
| `fraud.py`          | Fraud       | `FraudAssessment` — risk_score, siu_recommendation      |
| `email.py`          | Email       | `EmailThread` — metadata only, body excluded            |
| `documents.py`      | Documents   | `ClaimDocument[]` — received_date, page_count           |
| `errors.py`         | All         | `MockWriteDisabledError`, `MockNotFoundError`, etc.     |
| `simulation.py`     | All         | `SimulationConfig` — latency, 7 failure modes           |

---

## Backend — Integration Infrastructure

| Module                          | Sprint | Description                                           |
|---------------------------------|--------|-------------------------------------------------------|
| `integration/__init__.py`       | 0.5    | Package marker                                        |
| `integration/bootstrap.py`      | 3      | `_build_registry()`, `get_registry()` (lru_cache)    |
| `integration/config.py`         | 0.5    | Integration configuration                             |
| `integration/modes.py`          | 0.5    | `ProviderMode` enum (MOCK \| HYBRID \| REAL)          |
| `integration/registry.py`       | 3      | `ProviderRegistry` — register, resolve, singleton     |
| `integration/providers/__init__`| 3      | Provider base protocol                                |

---

## Backend — Supervisor (`backend/app/integration/supervisor/`)

| Module            | Description                                                   |
|-------------------|---------------------------------------------------------------|
| `__init__.py`     | Package: NOT agentic, NOT autonomous                          |
| `models.py`       | `SupervisorRequest`, `SupervisorResponse`, `GovernanceFlags`, `ClaimIntent`, `ProviderTrace` |
| `planner.py`      | Static intent→provider map + keyword classifier               |
| `executor.py`     | Registry-backed execution, one retry on retryable errors      |
| `aggregator.py`   | Merges provider results; email body excluded per ADR-006      |
| `governance.py`   | Pre-execution: `enforce_governance()` — checks writes + mock  |
| `supervisor.py`   | Core engine: classify → plan → govern → execute → aggregate   |

**Execution model:** INPUT → PLAN → GOVERNANCE → EXECUTE → AGGREGATE → RESPONSE

**Provider plan per intent:**

| Intent             | Providers                                        |
|--------------------|--------------------------------------------------|
| `claim_summary`    | claimcenter, policycenter, edw, fraud, email     |
| `coverage_analysis`| claimcenter, policycenter                        |
| `fraud_check`      | claimcenter, fraud                               |
| `document_review`  | documents                                        |
| `policy_lookup`    | policycenter, edw                                |

---

## Backend — Control Tower (`backend/app/integration/control_tower/`)

| Module          | Description                                                    |
|-----------------|----------------------------------------------------------------|
| `__init__.py`   | Package description                                            |
| `models.py`     | `ControlTowerRun`, `ControlTowerRunSummary`, `ControlTowerSummary`, `ControlTowerGovernanceSummary`, `ControlTowerProviderStep` |
| `trace_store.py`| Module-level `deque(maxlen=25)` ring buffer + thread lock      |
| `service.py`    | `SupervisorResponse → ControlTowerRun` conversion + queries    |

---

## Backend — Evaluation (`backend/app/integration/evaluation/`)

| Module              | Description                                                |
|---------------------|------------------------------------------------------------|
| `__init__.py`       | Package: isolated — nothing imports automatically          |
| `models.py`         | 9 model types: GoldenScenario, EvaluationResult, EvaluationScore, etc. |
| `golden_dataset.py` | 10 deterministic scenarios — no LLM, no prompts            |
| `scoring.py`        | 6-dimension engine — weights sum to 100 — pass threshold 80 |
| `metrics.py`        | 9 regression types — MISSING_PROVIDER through WRONG_SUCCESS_COUNT |
| `runner.py`         | Orchestrates scenario→supervisor→score→store (ring buffer 50)|
| `report.py`         | Builds `EvaluationResult` + promotion recommendation        |

---

## Backend — Validation (`backend/app/integration/validation/`)

| Module                  | Sprint | Description                                        |
|-------------------------|--------|----------------------------------------------------|
| `runner.py`             | 4      | Runs all adapter validators; produces `ValidationReport` |
| `contract_validator.py` | 4      | Verifies contract model structure                  |
| `response_validator.py` | 4      | Verifies mock response correctness                 |
| `error_validator.py`    | 4      | Verifies error handling (MockNotFoundError, etc.)  |
| `failure_injection.py`  | 4      | Tests 7 SimulationConfig failure modes             |

---

## Frontend Pages (`frontend/src/pages/`)

| Page                        | Route                              | Sprint | Description                     |
|-----------------------------|------------------------------------|--------|---------------------------------|
| `LoginPage.tsx`             | `/login`                           | 1      | Authentication screen           |
| `HomePage.tsx`              | `/home`                            | 1      | Claims list / workbench         |
| `ClaimSummaryPage.tsx`      | `/claims/:id/summary`              | 1      | AI claim summary                |
| `AssistantPage.tsx`         | `/claims/:id/assistant`            | 1      | Conversational AI assistant     |
| `DraftNotePage.tsx`         | `/claims/:id/draft-note`           | 1      | Governed note drafting          |
| `ApprovalPage.tsx`          | `/claims/:id/approval`             | 1      | Approval workflow               |
| `AuditTimelinePage.tsx`     | `/claims/:id/audit`                | 1      | Audit timeline                  |
| `ExecutiveDashboardPage.tsx`| `/dashboard`                       | 1      | Executive metrics dashboard     |
| `PlaceholderPage.tsx`       | Various                            | 1      | In-progress screen placeholder  |
| `ControlTowerPage.tsx`      | `/control-tower`                   | 6/6.1  | Execution observability + explorer |
| `AuditPage.tsx`             | (internal)                         | 1      | Audit detail                    |

---

## Test Suites (`backend/tests/`)

| File                    | Sprint | Checks | Scope                                         |
|-------------------------|--------|--------|-----------------------------------------------|
| `sprint5_validation.py` | 5      | 46     | Supervisor, planner, executor, governance, aggregator |
| `sprint6_validation.py` | 6      | 22     | Control Tower, trace store, ADR-006, ring buffer |
| `sprint7_validation.py` | 7      | 35     | Golden dataset, scoring, regression detection, runner |

Sprint 4 uses the internal `validation.runner` — no standalone test file.

---

## Documentation (`docs/`)

| File                             | Sprint | Contents                                      |
|----------------------------------|--------|-----------------------------------------------|
| `PHASE2_SUPERVISOR.md`           | 5      | Deterministic execution model, planner design |
| `PHASE2_CONTROL_TOWER.md`        | 6      | Observability philosophy, what is/isn't stored|
| `PHASE2_EVALUATION_FRAMEWORK.md` | 7      | Golden dataset, scoring, regression, promotion gate |
| `PHASE2A_COMPLETION_REPORT.md`   | 8      | This release — validation, governance, ADRs   |
| `PHASE2A_API_INVENTORY.md`       | 8      | All 27 API endpoints documented               |
| `PHASE2A_MODULE_INVENTORY.md`    | 8      | This file                                     |
| `PHASE2A_DEMO_GUIDE.md`          | 8      | Step-by-step leadership demo script           |
| `PHASE2B_BACKLOG.md`             | 8      | Phase 2B work items and entry criteria        |
