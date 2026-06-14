# Phase 2 Execution Plan — Enterprise Integration Foundation

**Branch:** `phase-2-enterprise-integration-foundation`
**Target:** Q3 2026
**Status:** Sprint 0 — Architecture Lockdown

---

## Objective

Connect the Enterprise AI Workbench to real enterprise systems — ClaimCenter, identity provider, model gateway, and knowledge store — while preserving the Phase 1 governance model, audit trail, and adjuster UX unchanged.

Phase 2 exits with:
1. Live read integrations against real ClaimCenter, real claim evidence, and real AI models
2. Pilot cohort of 10–15 adjusters processing real claims through the platform
3. Governed write framework ready for activation (pending final gate passage)
4. Evaluation harness operational with baseline metrics established
5. All ADR decisions resolved (OBO vs. fallback, write gate conditions met)

---

## Timeline Overview

```
2026
Q3: ─────────────────────────────────────────────────────────────────────
     Jul          Aug          Sep
     │            │            │
     S0  S1  S2   S3  S4  S5   S6  S7  PILOT
     │   │   │    │   │   │    │   │   │
     ▼   ▼   ▼    ▼   ▼   ▼    ▼   ▼   ▼
     ADR Auth Spec CC  VEC EVL  WFW WRT ─────────► PILOT GO-LIVE
```

Three parallel tracks run simultaneously across sprints:

| Track | Focus | Owner |
|-------|-------|-------|
| Track A — Integration | Adapter build, enterprise connectivity | Platform Engineering |
| Track B — AI/Evaluation | Prompt development, evaluation harness | AI/ML Engineering |
| Track C — Cross-functional | Identity, compliance, security, operations | IAM + Compliance + Security |

---

## Sprint Plan

### Sprint 0 — Architecture Lockdown (current)

**Duration:** 1 week
**Goal:** Lock all architectural decisions before integration work begins. No integration code written.

**Track A — Integration:**
- [ ] Publish ADR-001 through ADR-006 (this sprint)
- [ ] Identify specification sources for ClaimCenter, audit ledger
- [ ] Submit specification requests to Guidewire account team / IT

**Track B — AI/Evaluation:**
- [ ] Publish evaluation framework design (ADR-005)
- [ ] Draft synthetic test case schema (claim summary + evidence retrieval + draft note)

**Track C — Cross-functional:**
- [ ] Submit OBO feasibility request to IAM (ADR-003 trigger)
- [ ] Identify Compliance contact for golden dataset de-identification review (ADR-005)
- [ ] Identify SME adjuster volunteers for golden dataset labelling
- [ ] Confirm ClaimCenter lower-environment access timeline with IT

**Sprint 0 Exit Criteria:**
- [ ] All 6 ADRs published and reviewed by stakeholders
- [ ] OBO feasibility request submitted
- [ ] Specification requests submitted for all pending adapters
- [ ] Sprint 1 capacity confirmed

---

### Sprint 1 — Authentication Foundation

**Duration:** 2 weeks
**Goal:** Real adjuster authentication against the identity provider. Claim loading from ClaimCenter read API (first real read).

**Track A — Integration:**
- [ ] `IdentityAdapter` — implement SSO token validation against Okta/Azure AD
- [ ] `ClaimCenterReadAdapter` stub — `read_claim()` wired against ClaimCenter lower environment (specification-backed per ADR-004)
- [ ] Adapter integration tests against specification-backed mock ClaimCenter service
- [ ] Environment configuration: `mock | hybrid | real` runtime mode switch (reads from environment variable)

**Track B — AI/Evaluation:**
- [ ] Synthetic test case library v1 — 20 cases covering claim summary, evidence retrieval, draft note quality
- [ ] Evaluation engine scaffold — test execution harness, output schema validation, metrics computation

**Track C — Cross-functional:**
- [ ] OBO feasibility assessment received from IAM ← **ADR-003 gate**
- [ ] De-identification methodology draft submitted to Compliance
- [ ] ClaimCenter lower-environment sandbox credentials received

**Sprint 1 Exit Criteria:**
- [ ] Adjuster can authenticate against real identity provider in `hybrid` mode
- [ ] `read_claim()` returns real claim data from ClaimCenter lower environment for at least one test claim
- [ ] OBO feasibility decision received (enables or triggers fallback path in ADR-003)
- [ ] Runtime mode switch working: `PROVIDER_MODE=mock` and `PROVIDER_MODE=hybrid` both functional

---

### Sprint 2 — Specification Validation

**Duration:** 2 weeks
**Goal:** Validate all read adapter specifications against real ClaimCenter endpoints. No production data — lower environment only.

**Track A — Integration:**
- [ ] `ClaimCenterReadAdapter` — complete implementation of all read endpoints: `get_claim()`, `list_claim_notes()`, `get_claim_documents()`, `get_adjuster_portfolio()`
- [ ] Field mapping validation — map all ClaimCenter field names to platform domain model fields; document mappings in adapter
- [ ] Error handling — implement 404, 429, 503 handling per ClaimCenter specification
- [ ] `AuditLedgerAdapter` stub — interface wired, implementation pending specification (if specification not yet received, stub with `PENDING_SPEC`)

**Track B — AI/Evaluation:**
- [ ] Evaluation engine v1 — complete metric computation for claim summary quality and evidence retrieval quality
- [ ] First evaluation run against synthetic test cases with mock AI responses

**Track C — Cross-functional:**
- [ ] If OBO confirmed: begin OBO token exchange implementation
- [ ] If OBO denied: begin compliance approval process for service identity fallback (ADR-003)
- [ ] Compliance review of de-identification methodology ← external, may slip to Sprint 3

**Sprint 2 Exit Criteria:**
- [ ] All ClaimCenter read endpoints integrated and tested against lower environment
- [ ] Field mappings documented in adapter header
- [ ] Evaluation engine producing metrics from synthetic test cases
- [ ] Identity path confirmed (OBO or fallback)

---

### Sprint 3 — Vector Search + AI Provider

**Duration:** 2 weeks
**Goal:** Real evidence retrieval from Azure Cognitive Search. Real AI model calls via Azure OpenAI.

**Track A — Integration:**
- [ ] `VectorSearchAdapter` — implement `search_evidence(query, scope)` against Azure Cognitive Search (specification: Azure Cognitive Search REST API 2023-11-01)
- [ ] Evidence scope enforcement — claims-level isolation: `scope={claim_id}` filters prevent cross-claim evidence retrieval
- [ ] `AzureOpenAIAdapter` — implement `complete(messages, tools)` against Azure OpenAI (specification: Azure OpenAI REST API 2024-02-01)
- [ ] Model routing — governance engine outcome drives model selection: ALLOW → standard model; ESCALATE → senior-review model; DENY → no model call

**Track B — AI/Evaluation:**
- [ ] Prompt v1 — claim summary prompt, evidence retrieval prompt, draft note prompt
- [ ] Evaluation run with real AI model against synthetic test cases
- [ ] Baseline metrics established — claim summary quality, evidence retrieval quality, draft note quality

**Track C — Cross-functional:**
- [ ] SME adjuster volunteers confirmed and briefed
- [ ] Compliance de-identification approval received (target; may slip to Sprint 4)
- [ ] Security review of read-path token handling scheduled

**Sprint 3 Exit Criteria:**
- [ ] Evidence retrieval returning real documents from knowledge store for test claims
- [ ] AI model generating real claim summaries and draft notes
- [ ] Baseline evaluation metrics established against synthetic test cases
- [ ] Cross-claim evidence isolation confirmed by test

---

### Sprint 4 — Governance Calibration + Pilot Prep

**Duration:** 2 weeks
**Goal:** Governance engine calibrated against real data distribution. Pilot environment stood up.

**Track A — Integration:**
- [ ] `GovernanceAdapter` — wire governance engine evaluation against real policy configuration
- [ ] Governance threshold calibration against real claim type distribution from ClaimCenter lower environment
- [ ] Pilot environment configuration: `PROVIDER_MODE=real`, real identity, real ClaimCenter lower environment, real knowledge store
- [ ] Pilot environment smoke test — end-to-end claim workflow with real data, no production data

**Track B — AI/Evaluation:**
- [ ] Golden dataset v1 available (if Compliance approved de-identification) — integrate into evaluation engine
- [ ] Evaluation run with golden dataset (if available); continue with synthetic if not
- [ ] Prompt iteration based on evaluation results — target: hallucination rate ≤2%, evidence grounding ≥95%

**Track C — Cross-functional:**
- [ ] Security review of read path completed ← required for Sprint 5
- [ ] Pilot cohort identified: 10–15 adjusters with appropriate claim types in portfolio
- [ ] Pilot onboarding materials prepared: what the platform does, what "Ready for Write-back" means in Milestone 1
- [ ] Operations: Milestone 1 reconciliation process documented

**Sprint 4 Exit Criteria:**
- [ ] Governance engine calibrated: false positive ESCALATE rate ≤10%
- [ ] Pilot environment end-to-end smoke test passing with real data
- [ ] Pilot cohort confirmed and briefed
- [ ] Security read-path review complete

---

### Sprint 5 — Evaluation Harness + Adversarial Testing

**Duration:** 2 weeks
**Goal:** Evaluation harness operational. Adversarial injection test suite passing. Platform ready for pilot onboarding.

**Track A — Integration:**
- [ ] `AuditLedgerAdapter` — complete implementation (if specification received) or continue with platform-internal audit store
- [ ] Integration test suite complete — all read adapters tested against specification-backed mocks
- [ ] CI/CD gate: evaluation harness runs on every merge to `phase-2-enterprise-integration-foundation`

**Track B — AI/Evaluation:**
- [ ] Evaluation harness v1 complete — all five evaluation dimensions operational
- [ ] Regression detection operational — blocks deployment to pilot environment on metric drop >5pp
- [ ] Prompt injection adversarial test suite (ADR-006) — all 8 test categories passing

**Track C — Cross-functional:**
- [ ] Adversarial test suite review and sign-off by Security ← pilot onboarding gate
- [ ] Compliance sign-off on read-path audit trail ← pilot onboarding gate
- [ ] IAM sign-off on identity model in pilot environment ← pilot onboarding gate

**Sprint 5 Exit Criteria (Pilot Onboarding Gate):**
- [ ] Adversarial injection test suite passing — all 8 test categories
- [ ] Evaluation harness operational with metric baselines established
- [ ] Security sign-off on read path
- [ ] Compliance sign-off on audit trail
- [ ] IAM sign-off on identity model
- [ ] Operations reconciliation process active

---

### Sprint 6 — Pilot (Weeks 1–2)

**Duration:** 2 weeks
**Goal:** Pilot cohort live with real claims. Monitor quality, governance, and adjuster experience.

**Track A — Integration:**
- [ ] Production `real` mode activated for pilot cohort
- [ ] Write framework scaffold — `submit_note` tool registered with `enabled: false`; `WriteFrameworkNotEnabledError` raised and audited on any invocation attempt
- [ ] Monitoring: claim load time SLA (target: <2s), AI response time (target: <5s), governance evaluation time (target: <500ms)

**Track B — AI/Evaluation:**
- [ ] Weekly evaluation runs against pilot cohort claim subset (de-identified)
- [ ] Metric monitoring: hallucination rate, evidence grounding, confidence calibration
- [ ] Prompt adjustments based on pilot data (requires evaluation run to confirm improvement before deployment)

**Track C — Cross-functional:**
- [ ] Daily pilot feedback collection from adjuster cohort
- [ ] Write-gate progress: idempotency key implementation, reconciliation baseline, ClaimCenter write contract validation

**Sprint 6 Exit Criteria:**
- [ ] Pilot cohort processing real claims without platform errors
- [ ] All SLA targets met
- [ ] No security events of severity HIGH or above
- [ ] Write gate progress: ≥6 of 9 conditions satisfied

---

### Sprint 7 — Write Framework

**Duration:** 2 weeks
**Goal:** Write framework gate passage. First real write to ClaimCenter in lower environment (not pilot production).

**Track A — Integration:**
- [ ] `ClaimCenterWriteAdapter` — implement `submit_note()` against ClaimCenter write specification
- [ ] Idempotency key implementation — platform-generated UUID per note submission; ClaimCenter duplicate detection confirmed
- [ ] Read-back reconciliation — retrieve submitted note after write; verify content match
- [ ] Write rollback procedure — documented, tested against ClaimCenter lower environment

**Track B — AI/Evaluation:**
- [ ] Evaluation run specifically on draft notes that were approved and submitted — note quality vs. adjuster-modified rate
- [ ] Confidence score vs. adjuster approval rate correlation analysis

**Track C — Cross-functional:**
- [ ] Security review of write path: token handling, note content injection surface, rate limiting ← write gate condition
- [ ] Compliance sign-off on write audit trail ← write gate condition
- [ ] IAM approval of write endpoint access ← write gate condition
- [ ] Operations rollback procedure approval ← write gate condition

**Sprint 7 Exit Criteria (Write Gate):**
- [ ] All 9 write-milestone exit gate conditions satisfied (ADR-002)
- [ ] `submit_note` tool activated in lower environment
- [ ] First real note written to ClaimCenter lower environment
- [ ] Read-back reconciliation passing

---

### Pilot (Extended) — Write-Back Activation

**Duration:** Ongoing into Q4
**Goal:** Write-back activated for pilot cohort. Pilot expanded.

- [ ] `submit_note` tool enabled in pilot environment
- [ ] Pilot cohort notes written to ClaimCenter — adjuster no longer submits notes via manual process in parallel
- [ ] Dual-workflow reconciliation ends
- [ ] Pilot expanded to additional adjuster cohort
- [ ] Phase 3 planning begins

---

## Measurable Exit Gates

Phase 2 is complete when all five exit gates are satisfied:

| Gate | Condition | Metric |
|------|-----------|--------|
| G1 — Live Read | Real claims processed end-to-end without mock data fallback | ≥200 claims processed in pilot |
| G2 — AI Quality | Evaluation harness confirms AI quality above threshold | Hallucination ≤2%, grounding ≥95%, note approval ≥70% |
| G3 — Governance Calibration | Governance engine calibrated on real data | False positive ESCALATE ≤10%, false negative ≤2% |
| G4 — Write Framework | Write gate satisfied, first real ClaimCenter write successful | ≥1 approved note written to ClaimCenter lower environment |
| G5 — Pilot Satisfaction | Adjuster cohort feedback confirms platform reduces effort | ≥80% of pilot adjusters report time savings on AI-assisted claims |

---

## Risk Summary

See [PHASE2_RISK_RETIREMENT_MATRIX.md](PHASE2_RISK_RETIREMENT_MATRIX.md) for the full risk register with retirement conditions and escalation paths.

Top 3 risks by expected impact on timeline:

| Risk | Timeline Impact | Mitigation |
|------|----------------|------------|
| OBO infeasible — IAM cannot approve OBO grant | +1–2 sprints (fallback compliance approval) | ADR-003 fallback path defined; Compliance briefed in Sprint 0 |
| ClaimCenter specification not available — Guidewire spec request delayed | +1–2 sprints per blocked adapter | `PENDING_SPEC` stubs; parallel work on unblocked adapters |
| Golden dataset delayed — Compliance approval takes longer than Sprint 3 | Pilot evaluation uses synthetic only; golden dataset integrated after pilot | Evaluation engine decoupled from golden dataset (ADR-005) |

---

## Architecture References

| Decision | ADR |
|----------|-----|
| Supervisor + Deterministic Tools | [ADR-001](adr/ADR-001-supervisor-tools.md) |
| Read-Before-Write Milestone Separation | [ADR-002](adr/ADR-002-read-before-write.md) |
| Identity OBO / Fallback | [ADR-003](adr/ADR-003-identity-obo-fallback.md) |
| Contract-First Integration | [ADR-004](adr/ADR-004-contract-first-integration.md) |
| Evaluation-First AI | [ADR-005](adr/ADR-005-evaluation-first-ai.md) |
| Untrusted Content Isolation | [ADR-006](adr/ADR-006-untrusted-content-isolation.md) |
