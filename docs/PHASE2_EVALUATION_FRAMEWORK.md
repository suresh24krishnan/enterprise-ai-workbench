# Phase 2 Evaluation Framework

**Sprint 7 — Evaluation Harness & Golden Dataset**
**Branch:** `phase-2-enterprise-integration-foundation`
**Status:** Active — deterministic evaluation, 10 golden scenarios, 6-dimension scoring

---

## Purpose

Every provider, prompt, model, or supervisor change that enters this system must
pass a deterministic quality gate before it can be promoted. The Evaluation
Framework is that gate.

Without it:
- A planner change that drops a provider goes undetected until production.
- A governance regression (writes_enabled=True) reaches Phase 2B.
- A latency spike from a real adapter is invisible until demo day.
- "It worked in my test" is the only evidence of correctness.

With it:
- 10 deterministic golden scenarios define what "correct" means.
- 6 weighted scoring dimensions produce a 0–100 quality score.
- A regression engine detects every category of deviation.
- A promotion recommendation (PROMOTE / BLOCK / REVIEW) is generated per run.
- All results are JSON-serializable and API-queryable.

---

## Golden Dataset Philosophy

A golden scenario is a contract: given this claim_id and this intent,
the supervisor MUST select exactly these providers, in this order,
with exactly this success count, with writes disabled, in mock mode,
within the latency limit.

Golden scenarios do NOT contain:
- LLM outputs
- Prompt text
- Natural language descriptions of expected behavior
- Any non-deterministic element

They contain only typed, machine-verifiable expectations:

```python
GoldenExpectation(
    expected_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    expected_provider_count=5,
    expected_success_count=5,
    writes_expected=False,
    real_providers_expected=False,
    max_latency_ms=500.0,
    execution_order_strict=True,
)
```

This means evaluation is repeatable by anyone, on any machine, at any time,
without access to a running model.

---

## 10 Golden Scenarios

| ID     | Name                              | Intent             | Providers | Tags            |
|--------|-----------------------------------|--------------------|-----------|-----------------|
| GS-001 | Claim Summary — Full Provider Set | claim_summary      | 5         | smoke, full     |
| GS-002 | Coverage Analysis                 | coverage_analysis  | 2         | coverage        |
| GS-003 | Fraud Review                      | fraud_check        | 2         | fraud           |
| GS-004 | Document Search                   | document_review    | 1         | documents       |
| GS-005 | Policy Lookup                     | policy_lookup      | 2         | policy          |
| GS-006 | Customer Profile (High-Value)     | claim_summary      | 5         | customer        |
| GS-007 | Email Metadata                    | claim_summary      | 5         | email-metadata  |
| GS-008 | Reserve Review                    | coverage_analysis  | 2         | reserve         |
| GS-009 | Timeline Review                   | fraud_check        | 2         | timeline        |
| GS-010 | Multi-Provider Determinism Check  | claim_summary      | 5         | determinism     |

---

## Deterministic Scoring

Six dimensions produce a 0–100 overall score. No AI. No randomness.

| Dimension                  | Weight | Measures                                   |
|----------------------------|--------|--------------------------------------------|
| Provider Selection Accuracy| 25     | Jaccard similarity: expected vs actual set  |
| Execution Success Rate     | 20     | succeeded_count / provider_count            |
| Governance Compliance      | 20     | mode=mock AND writes=False                  |
| Write Safety               | 15     | writes_enabled=False always                 |
| Latency                    | 10     | actual_ms <= max_latency_ms                 |
| Determinism                | 10     | Execution order matches expectation         |
| **Total**                  | **100**|                                             |

**Pass threshold: 80 / 100**

A run passes only if:
1. overall_score >= 80.0
2. No critical regressions

---

## Regression Detection

The regression engine compares actual supervisor output to the golden expectation
and classifies every deviation:

| Regression Type         | Severity | Example                                        |
|-------------------------|----------|------------------------------------------------|
| MISSING_PROVIDER        | critical | fraud provider not selected for fraud_check    |
| UNEXPECTED_PROVIDER     | warning  | documents selected for claim_summary           |
| PROVIDER_FAILURE        | critical | 3/5 providers succeeded when 5/5 expected      |
| WRITE_ENABLED           | critical | writes_enabled=True (never acceptable in 2A)   |
| REAL_PROVIDER_ENABLED   | critical | provider_mode=hybrid instead of mock           |
| LATENCY_EXCEEDED        | warning  | 520ms vs 500ms limit                           |
| WRONG_EXECUTION_ORDER   | warning  | [fraud, claimcenter] instead of [claimcenter, fraud] |
| WRONG_PROVIDER_COUNT    | critical | 4 providers selected instead of 5              |
| WRONG_SUCCESS_COUNT     | warning  | 6 successes when 5 expected                    |

Any critical regression → **BLOCK** (do not promote regardless of score).

---

## Promotion Gate

Each evaluation run produces one of three recommendations:

- **PROMOTE** — Score >= 80, no critical regressions. Safe for Phase 2B.
- **BLOCK** — One or more critical regressions. Do not promote.
- **REVIEW** — Score < 80 but no critical regressions. Investigate before promoting.

The recommendation is available at:
`GET /api/integration/evaluation/report/{run_id}/recommendation`

---

## API Reference

```
GET  /api/integration/evaluation/scenarios
     Returns: list[GoldenScenario] — all 10 scenarios

POST /api/integration/evaluation/run
     Body: { "scenario_id": "GS-001" }
     Returns: EvaluationResult — full scored report

GET  /api/integration/evaluation/report/{run_id}
     Returns: EvaluationResult
     Errors: 404 if not in store (in-memory, cleared on restart)

GET  /api/integration/evaluation/report/{run_id}/recommendation
     Returns: { run_id, recommendation }

GET  /api/integration/evaluation/runs
     Returns: list[EvaluationRun] — newest first

GET  /api/integration/evaluation/summary
     Returns: EvaluationSummary — aggregate health
```

All endpoints are **read-only**. No writes. No side effects beyond storing
the result in the in-memory store.

---

## Future: Real Provider Validation (Phase 2B)

When real Guidewire adapters are registered:

1. Run the same golden scenarios against HYBRID mode.
2. The scoring engine is unchanged — only provider_mode changes.
3. Real adapters will show latency > 100ms; the 500ms limit accommodates this.
4. A new tag `real-provider` will mark scenarios that target HYBRID/REAL mode.
5. The promotion gate applies identically — the same 80/100 threshold.

The framework validates mock correctness now so that switching to real adapters
later requires zero changes to the evaluation layer.

---

## Future: Hybrid Mode Validation

In HYBRID mode (some real, some mock):

1. Scenarios are tagged with which providers are expected to be real.
2. The regression engine checks provider_mode per step (requires extending
   ProviderTrace to expose mode per provider — Phase 2B enhancement).
3. The governance dimension checks that real providers are only used where
   explicitly enabled.

---

## Phase 2B Readiness

The evaluation framework establishes the quality baseline for Phase 2B entry:

1. All 10 golden scenarios must PASS before Phase 2B begins.
2. A new golden scenario set (GS-101 to GS-110) will cover real adapter behavior.
3. The write gate opens only when Phase 2B validation shows writes_safe=True
   across all write-path scenarios.
4. The Control Tower shows current evaluation health alongside execution traces.

---

## Module Structure

```
backend/app/integration/evaluation/
  __init__.py         — package description
  models.py           — all evaluation data models (pure Pydantic)
  golden_dataset.py   — 10 deterministic scenarios (no LLM, no prompts)
  scoring.py          — 6-dimension deterministic scoring engine
  metrics.py          — regression detection engine
  runner.py           — orchestrates scenario → supervisor → score → store
  report.py           — assembles EvaluationResult + recommendation

backend/app/api/
  routes_evaluation.py — 6 HTTP endpoints

frontend/src/pages/
  ControlTowerPage.tsx — Latest Evaluation section (read-only)

docs/
  PHASE2_EVALUATION_FRAMEWORK.md  — this file
```

---

## Write Gate Status

Writes remain disabled. The evaluation framework never enables writes.
It reads supervisor outputs and scores them. No write path is touched.

`EvaluationSummary.writes_enabled` is always `false`.
