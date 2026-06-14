# ADR-005 — Evaluation-First AI Integration

**Status:** Accepted
**Date:** 2026-06-13
**Phase:** 2 — Enterprise Integration Foundation
**Deciders:** Platform Architecture Team, AI/ML Engineering
**Supersedes:** None

---

## Context

Phase 1 used mock AI responses — deterministic outputs that demonstrated the workflow without measuring model quality. Phase 2 introduces real AI model calls (Azure OpenAI or equivalent) against real claim data. The question is: how do we know when the AI is performing adequately, and how do we catch regressions?

Without an evaluation framework:
- AI quality is assessed subjectively by reading outputs during QA
- Model upgrades or prompt changes may improve one capability while degrading another, with no systematic detection
- Confidence scores are not validated against actual accuracy
- Evidence citation quality cannot be measured
- The governance engine's ESCALATE threshold cannot be calibrated against real outcome data

Two approaches were considered:

**Approach A — Ship first, evaluate later:** Deploy Phase 2 with real AI calls, collect feedback from adjusters during pilot, build evaluation infrastructure after the pilot produces enough data.

**Approach B — Evaluation-first:** Build the evaluation harness early in Phase 2. Use it to validate prompt quality before pilot, catch regressions during model upgrades, and calibrate the governance engine's confidence thresholds against real outcomes.

---

## Decision

**Phase 2 adopts evaluation-first AI integration. The evaluation harness is built in Sprint 5 and is operational before the pilot cohort is onboarded.**

The evaluation harness has two components with different readiness timelines:

### Component 1 — Evaluation Engine (buildable now)

The evaluation engine is the infrastructure for running evaluations: prompt execution, output scoring, metric computation, regression detection, and reporting. It has no dependency on real claim data, real adjuster decisions, or compliance approval.

The evaluation engine can be built and tested against synthetic data immediately. It is the platform's mechanism for answering: "is the AI performing at the required quality level?"

### Component 2 — Golden Dataset (external dependency)

The golden dataset is a set of real (de-identified) claim cases with known correct outputs — expert adjuster assessments, correct coverage positions, accurate draft notes — against which the evaluation engine scores AI outputs.

**The golden dataset cannot be built without:**
- Compliance approval for de-identification methodology
- SME (Subject Matter Expert) adjuster participation to provide correct labels
- Legal review of what constitutes appropriate claim data use for model evaluation

The golden dataset is a Phase 2 external dependency. Work on it begins in Sprint 0 (stakeholder identification) but completion depends on Compliance and SME timelines that are outside the engineering team's control.

**These two components must not be conflated.** The evaluation engine is an engineering deliverable. The golden dataset is a cross-functional deliverable. Blocking the evaluation engine on the golden dataset is the wrong dependency direction.

---

## Evaluation Dimensions

The evaluation engine scores AI outputs across five dimensions:

### 1. Claim Summary Quality

| Metric | Description | Target |
|--------|-------------|--------|
| Evidence grounding rate | % of claims where every summary statement is supported by a cited evidence source | ≥95% |
| Coverage position accuracy | % of summaries where the coverage position matches the expert adjuster assessment | ≥90% |
| Hallucination rate | % of summaries containing statements not supported by any retrieved evidence | ≤2% |
| Confidence calibration | Correlation between AI confidence score and expert-assessed accuracy | r ≥ 0.80 |

### 2. Evidence Retrieval Quality

| Metric | Description | Target |
|--------|-------------|--------|
| Recall@5 | % of relevant documents appearing in the top 5 retrieved results | ≥85% |
| Precision@5 | % of top 5 retrieved results that are relevant | ≥80% |
| Missing document rate | % of evaluations where a key document was not retrieved | ≤5% |

### 3. Draft Note Quality

| Metric | Description | Target |
|--------|-------------|--------|
| Factual accuracy | % of note statements that are factually consistent with the claim record | ≥95% |
| Format conformance | % of notes that conform to the standard adjuster note template | ≥98% |
| Expert approval rate | % of AI draft notes that an expert adjuster would approve without modification | ≥70% (Phase 2 target) |

### 4. Governance Engine Calibration

| Metric | Description | Target |
|--------|-------------|--------|
| False positive rate (ESCALATE) | % of cases escalated that a senior adjuster would have processed normally | ≤10% |
| False negative rate (ALLOW when ESCALATE warranted) | % of cases allowed that a senior adjuster would have escalated | ≤2% |
| DENY accuracy | % of DENY decisions that a compliance reviewer agrees with | ≥95% |

### 5. Regression Detection

The evaluation engine runs on every prompt change, model version upgrade, and retrieval configuration change. A regression is defined as:
- Any metric dropping more than 5 percentage points from the prior baseline
- Hallucination rate increasing above the target threshold
- Confidence calibration correlation dropping below 0.75

A regression blocks the change from being deployed to the pilot environment until the root cause is identified and resolved.

---

## Evaluation Architecture

```
┌──────────────────────────────────────────────────────┐
│                EVALUATION HARNESS                    │
│                                                      │
│  ┌─────────────┐    ┌──────────────┐                 │
│  │ Test Cases  │    │  Evaluation  │                 │
│  │ (synthetic  │───▶│   Engine     │                 │
│  │  + golden)  │    │              │                 │
│  └─────────────┘    │  - Execute   │                 │
│                     │  - Score     │                 │
│  ┌─────────────┐    │  - Compare   │                 │
│  │  AI System  │◀───│  - Report    │                 │
│  │  (under     │    └──────┬───────┘                 │
│  │   test)     │           │                         │
│  └─────────────┘    ┌──────▼───────┐                 │
│                     │   Metrics    │                 │
│                     │   Store      │                 │
│                     └──────┬───────┘                 │
│                            │                         │
│                     ┌──────▼───────┐                 │
│                     │  Regression  │                 │
│                     │  Detector    │                 │
│                     └─────────────┘                 │
└──────────────────────────────────────────────────────┘
```

The evaluation harness is a standalone module — it does not run inside the application runtime. It is invoked:
- Manually by engineers after prompt changes
- Automatically in CI/CD before deployment to the pilot environment
- Periodically (weekly) against the production model to detect model drift

---

## Golden Dataset — Acquisition Plan

| Step | Action | Owner | Timeline |
|------|--------|-------|----------|
| 1 | Identify Compliance contact for de-identification review | Platform Lead | Sprint 0 |
| 2 | Draft de-identification methodology for review | Platform Engineering | Sprint 1 |
| 3 | Identify SME adjuster volunteers (target: 3–5 senior adjusters) | Claims Operations | Sprint 1 |
| 4 | Compliance approval of de-identification methodology | Compliance | Sprint 2–3 (external) |
| 5 | SME labelling of initial golden cases (target: 50 cases) | SME Adjusters | Sprint 3–4 (external) |
| 6 | First golden dataset version available for evaluation harness | Platform Engineering | Sprint 4–5 |

The evaluation harness begins operation with synthetic test cases in Sprint 5. The golden dataset is integrated when available. The pilot cohort is not blocked on the golden dataset — synthetic evaluation is sufficient to confirm AI quality before pilot onboarding.

---

## Consequences

**Positive:**
- AI quality is measurable and regression-detectable before pilot onboarding
- Model upgrades can be evaluated systematically rather than subjectively
- Governance engine calibration is data-driven rather than rule-of-thumb
- Confidence scores are validated against actual accuracy — adjusters can trust the confidence indicator

**Negative:**
- Golden dataset acquisition is an external dependency with uncertain timelines
- Evaluation harness build is a Sprint 5 commitment that competes with adapter build work in the same timeframe
- Synthetic test cases may not capture the full distribution of real claim types, creating evaluation blind spots until the golden dataset is available

**Mitigation:**
- Evaluation engine is decoupled from golden dataset — synthetic evaluation begins immediately
- Golden dataset acquisition is tracked as a risk item in the risk retirement matrix with weekly escalation cadence if Compliance approval is delayed

---

## Review Trigger

This ADR should be reviewed if:
- Compliance rejects the proposed de-identification methodology, requiring a different dataset strategy
- The golden dataset is available earlier than expected, allowing earlier calibration
- A third-party evaluation framework (e.g., RAGAS, TruLens, LangSmith) is adopted that changes the evaluation architecture
