# Phase 2 Risk Retirement Matrix

**Branch:** `phase-2-enterprise-integration-foundation`
**Last Updated:** 2026-06-13
**Owner:** Platform Architecture Team

---

## Overview

This matrix tracks the 10 principal risks for Phase 2 integration. For each risk:
- **Status** moves from OPEN → ACTIVE → RETIRED as retirement conditions are met
- **Sprint Target** is when retirement is expected
- **Escalation Path** defines who decides if retirement is blocked past the target sprint

Risks are reviewed weekly in the Phase 2 standup. Any risk that has not progressed in two consecutive sprint reviews is escalated per its escalation path.

---

## Risk Register

### R1 — OBO Identity Infeasibility

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | External Dependency — IAM |
| **ADR** | ADR-003 |
| **Sprint Target** | Sprint 1 |
| **Severity** | HIGH |
| **Probability** | MEDIUM |

**Description:**
The OAuth 2.0 On-Behalf-Of flow requires that ClaimCenter be registered as a resource application in the enterprise identity provider (Azure AD / Okta) and that the platform service principal be granted delegated `ClaimCenter.Read` and `ClaimCenter.Write` scopes. Enterprise IAM teams frequently cannot approve these grants within a project's timeline due to security review queues, vendor registration requirements, or policy restrictions on delegated token exchange.

If OBO is infeasible, the fallback (governed service identity with immutable user attribution — ADR-003 Model B) requires explicit Compliance approval before the write path can be activated. This creates a secondary dependency on Compliance that may extend the write-gate timeline by 1–3 sprints.

**Impact if unretired:**
- Write framework (ADR-002 Milestone 2) cannot advance until identity model is resolved
- If both OBO and fallback approval are delayed past Sprint 3, the write gate cannot be satisfied in Phase 2
- Phase 2 ships read-only — still valuable, but write-back is deferred to Phase 3

**Retirement Conditions:**
One of the following must be true:
- [ ] OBO feasibility confirmed by IAM: prerequisites in ADR-003 satisfied, OBO token exchange tested against ClaimCenter sandbox
- [ ] OBO confirmed infeasible by IAM AND Compliance has explicitly approved the service identity fallback model per ADR-003

**Escalation Path:**
Sprint 1 end: no IAM response → Platform Lead escalates to IT Director
Sprint 2 end: IAM confirms OBO infeasible, Compliance approval not yet obtained → Platform Lead escalates to Chief Compliance Officer
Sprint 3 end: neither condition met → Phase 2 ships read-only; write framework deferred to Phase 3

**Weekly Check:**
- IAM OBO feasibility request submitted: ☐ (Sprint 0 action)
- IAM response received: ☐
- Compliance briefed on fallback model: ☐

---

### R2 — ClaimCenter Specification Unavailable

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | External Dependency — Guidewire / IT |
| **ADR** | ADR-004 |
| **Sprint Target** | Sprint 2 |
| **Severity** | HIGH |
| **Probability** | MEDIUM |

**Description:**
The contract-first integration policy (ADR-004) requires that all adapter implementations be derived from published API specifications. The Guidewire ClaimCenter REST API specification may require an NDA, a licensed developer portal login, or a formal support request — none of which the platform engineering team can initiate unilaterally. If the specification is not available by Sprint 2, the ClaimCenter read adapter cannot be completed, and the Sprint 3 vector search + AI integration depends on having claim data to retrieve evidence for.

**Impact if unretired:**
- `ClaimCenterReadAdapter` cannot be completed per ADR-004 contract-first policy
- Sprint 3 AI integration is blocked — cannot retrieve real evidence without real claim data
- Pilot onboarding (Sprint 5/6) is blocked

**Retirement Conditions:**
- [ ] Guidewire ClaimCenter REST API specification received (developer portal access granted OR documentation package received from Guidewire account team)
- [ ] Specification reviewed and field mappings to platform domain model drafted
- [ ] At least `get_claim()` and `list_claim_notes()` endpoints validated against lower-environment ClaimCenter

**Escalation Path:**
Sprint 1 end: no specification received → Platform Lead escalates to IT Director with explicit dependency statement
Sprint 2 start: still no specification → request Guidewire account team direct engagement via enterprise relationship
Sprint 2 end: still no specification → evaluate specification-lite exception: build against ClaimCenter OpenAPI explorer if available in lower environment; document deviation from ADR-004 in ADR-004 status note

**Weekly Check:**
- Guidewire account team contact identified: ☐ (Sprint 0 action)
- Specification request submitted: ☐
- Lower-environment ClaimCenter sandbox access confirmed: ☐

---

### R3 — Golden Dataset Compliance Approval Delayed

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | External Dependency — Compliance / Legal |
| **ADR** | ADR-005 |
| **Sprint Target** | Sprint 4 |
| **Severity** | MEDIUM |
| **Probability** | HIGH |

**Description:**
The golden dataset requires de-identified real claim cases. De-identification must be approved by Compliance to ensure the methodology meets regulatory requirements for data use in AI model evaluation. Compliance review timelines are externally controlled and frequently exceed project estimates. SME adjuster availability for labelling is also externally controlled.

**Impact if unretired:**
- Evaluation harness operates on synthetic test cases only through the pilot period
- Governance engine calibration cannot be data-driven before pilot onboarding
- Post-pilot evaluation quality is limited

**Mitigation (why this is MEDIUM not HIGH):**
Per ADR-005, the evaluation engine is decoupled from the golden dataset. The pilot cohort is not blocked on the golden dataset — synthetic evaluation is sufficient to confirm AI quality before pilot onboarding. The golden dataset improves evaluation quality; it does not gate pilot onboarding.

**Retirement Conditions:**
- [ ] Compliance approves de-identification methodology
- [ ] 50 claim cases de-identified and prepared for labelling
- [ ] SME adjusters complete labelling of ≥40 cases
- [ ] Golden dataset v1 integrated into evaluation engine

**Escalation Path:**
Sprint 3 end: Compliance approval not received → Platform Lead notifies Compliance of evaluation timeline dependency; requests expedited review
Sprint 4 end: still no approval → evaluation harness ships with synthetic only; golden dataset tracked as Phase 2 extension deliverable

**Weekly Check:**
- Compliance contact identified: ☐ (Sprint 0 action)
- De-identification methodology draft submitted: ☐ (Sprint 1 action)
- SME volunteers confirmed: ☐ (Sprint 1 action)
- Compliance review received: ☐

---

### R4 — ClaimCenter Write Endpoint Access Unavailable

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | External Dependency — IT / IAM / Network |
| **ADR** | ADR-002 |
| **Sprint Target** | Sprint 7 |
| **Severity** | HIGH |
| **Probability** | MEDIUM |

**Description:**
Write access to ClaimCenter requires network/firewall approval, IAM service account provisioning for write scopes, and security review of the write endpoint. These approvals typically require IT change management and may involve change advisory board review. If write access to the lower environment is not approved by Sprint 7, the write framework cannot be validated before the write gate is passed.

**Impact if unretired:**
- Write gate (ADR-002) cannot be satisfied
- Phase 2 ships read-only
- Write-back deferred to Phase 3

**Mitigation:**
Per ADR-002, Phase 2 read-only is a valid outcome — the platform is valuable without write-back. Write-back being deferred does not block pilot onboarding or Phase 2 completion.

**Retirement Conditions:**
- [ ] IAM service account provisioned with ClaimCenter write scopes in lower environment
- [ ] Network/firewall rules approved for write endpoint access from platform deployment environment
- [ ] Security review of write path completed (ADR-002 write gate condition)
- [ ] `submit_note()` tested against ClaimCenter lower environment

**Escalation Path:**
Sprint 5: no write access approved → Platform Lead escalates to IT Director with write gate dependencies listed
Sprint 6 end: still no access → Write framework deferred; Phase 2 ships read-only; write-back becomes Phase 3 Sprint 1 priority

**Weekly Check:**
- IAM write scope request submitted: ☐
- Network access request submitted: ☐
- Security write-path review scheduled: ☐

---

### R5 — Prompt Injection in Retrieved Content

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | Security |
| **ADR** | ADR-006 |
| **Sprint Target** | Sprint 5 |
| **Severity** | CRITICAL |
| **Probability** | MEDIUM |

**Description:**
Retrieved claim documents — from ClaimCenter, the vector store, email attachments, and medical reports — originate from external parties who may embed adversarial text designed to manipulate the AI supervisor. A successful injection could cause the supervisor to produce incorrect outputs, trigger incorrect governance decisions, or (in the write-enabled phase) cause an incorrect note to be written to ClaimCenter.

**Impact if unretired:**
- Incorrect AI outputs presented to adjusters as authoritative analysis
- Governance decisions manipulated by attacker-controlled document content
- In write-enabled phase: regulatory event if an injected note is written to ClaimCenter

**Retirement Conditions:**
- [ ] Structural isolation implemented in orchestration service (ADR-006 Layer 1)
- [ ] Supervisor instruction hardening implemented (ADR-006 Layer 2)
- [ ] Output validation operational (ADR-006 Layer 3)
- [ ] Tool-level write controls confirmed (ADR-006 Layer 4)
- [ ] Adversarial test suite passing — all 8 test categories (ADR-006 Layer 5)
- [ ] Security sign-off on adversarial test results

**Escalation Path:**
Sprint 5 end: adversarial test suite not passing → Pilot onboarding blocked; Security and Platform Engineering resolve failing categories before pilot
Sprint 6 start: still failing → Escalate to CISO; pilot delayed

**Weekly Check:**
- Structural isolation implementation started: ☐
- Adversarial test suite authored: ☐ (Security)
- Test suite execution scheduled for Sprint 5: ☐

---

### R6 — AI Hallucination Rate Above Threshold

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | AI Quality |
| **ADR** | ADR-005 |
| **Sprint Target** | Sprint 5 |
| **Severity** | HIGH |
| **Probability** | MEDIUM |

**Description:**
The evaluation harness may find that the AI supervisor's claim summaries contain statements not supported by retrieved evidence at a rate above the 2% threshold. This could be caused by the base model's tendency to interpolate from training data, poor evidence retrieval quality (ADR-005 retrieval metrics), or prompt design issues. A hallucination rate above threshold means adjusters cannot rely on AI-generated summaries — undermining the platform's core value proposition.

**Impact if unretired:**
- Pilot cohort cannot use AI summaries as a starting point — must verify every statement independently
- Adjuster time savings are not realised
- Regulatory risk: an adjuster approves a summary containing a hallucinated fact

**Retirement Conditions:**
- [ ] Evaluation harness confirms hallucination rate ≤2% on synthetic test cases
- [ ] Hallucination rate ≤2% confirmed on golden dataset (when available)
- [ ] Evaluation run on pilot cohort claim subset confirms ≤2% hallucination rate

**Escalation Path:**
Sprint 5 end: hallucination rate >2% → AI/ML Engineering initiates prompt redesign; pilot onboarding delayed until threshold met
Sprint 6 end: still above threshold → Evaluate model upgrade or retrieval quality improvement; escalate to Platform Lead

**Weekly Check:**
- Current hallucination rate from synthetic evaluation: ☐
- Prompt version under test: ☐

---

### R7 — ClaimCenter Lower Environment Unavailability

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | Infrastructure |
| **ADR** | ADR-004 |
| **Sprint Target** | Sprint 1 |
| **Severity** | MEDIUM |
| **Probability** | LOW |

**Description:**
ClaimCenter lower environments (dev/test/staging) are shared resources that may experience scheduled maintenance windows, unplanned outages, or data refreshes that make the environment unavailable during critical integration sprints. Sprint 1 and Sprint 2 have the highest dependency on lower-environment availability.

**Mitigation:**
Specification-backed mock ClaimCenter service (ADR-004) allows adapter development to proceed when the real lower environment is unavailable. Integration tests run against the mock service in CI/CD and only require the real environment for validation runs.

**Retirement Conditions:**
- [ ] ClaimCenter lower environment access confirmed and baseline connectivity test passing
- [ ] Maintenance window schedule obtained from IT
- [ ] Mock ClaimCenter service validated against lower environment (at least 3 endpoints)

**Escalation Path:**
Sprint 1 end: no lower environment access → Platform Lead escalates to IT; continue adapter build against mock service
Sprint 2 end: still no access → Re-evaluate Sprint 3 dependency; consider using ClaimCenter sandbox if lower environment is unavailable

**Weekly Check:**
- Lower environment URL and credentials received: ☐
- Maintenance window schedule received: ☐
- Connectivity test passing: ☐

---

### R8 — Adjuster Adoption Failure

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | Change Management |
| **ADR** | None — operational risk |
| **Sprint Target** | Sprint 6 (Pilot) |
| **Severity** | HIGH |
| **Probability** | MEDIUM |

**Description:**
Pilot adjusters may find the platform does not fit their workflow, produces AI outputs that require more correction than the time saved, or creates uncertainty about the "Ready for Write-back" state during Milestone 1. If ≥50% of pilot adjusters report no time savings, the platform's business case is not validated and Phase 3 expansion is at risk.

**Impact if unretired:**
- Business case not validated — Phase 3 expansion stalled
- Leadership confidence in the platform reduced
- Risk of platform being deprioritised before write-back is activated

**Retirement Conditions:**
- [ ] ≥80% of pilot adjusters report time savings on AI-assisted claims (exit gate G5)
- [ ] Median claim processing time for AI-assisted claims is measurably lower than baseline
- [ ] Adjuster feedback identifies no unresolved workflow blockers

**Escalation Path:**
Sprint 6 mid-point: early feedback negative → Claims Operations conducts structured interviews; identify and resolve specific blockers before sprint end
Sprint 7 start: adoption still low → Platform Lead presents findings to leadership; consider extended pilot period with workflow adjustments before Phase 3 decision

**Weekly Check:**
- Pilot cohort confirmed and briefed: ☐
- Feedback collection mechanism active: ☐
- Weekly adoption metric tracked: ☐

---

### R9 — Write Idempotency Failure

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | Data Integrity |
| **ADR** | ADR-002 |
| **Sprint Target** | Sprint 7 |
| **Severity** | CRITICAL |
| **Probability** | LOW |

**Description:**
If the idempotency key mechanism fails — due to key generation collision, ClaimCenter duplicate detection not working as expected, or a network retry submitting a note twice — a duplicate note appears in the claim record. A duplicate adjuster note in ClaimCenter is a regulated event: it must be voided by a ClaimCenter administrator and logged as a data quality incident.

**Mitigation:**
Write framework is disabled (ADR-002) until idempotency is confirmed in lower environment. The idempotency check is a mandatory write-gate condition — not optional.

**Retirement Conditions:**
- [ ] Platform idempotency key generation implemented (UUID v4, per-submission unique)
- [ ] ClaimCenter duplicate note detection confirmed against lower environment — submit same note twice with same idempotency key, confirm second submission is rejected
- [ ] Network retry behaviour tested — connection reset mid-write, retry with same idempotency key, confirm single note in ClaimCenter
- [ ] Idempotency behaviour documented in write rollback procedure

**Escalation Path:**
Sprint 7: duplicate note created in lower environment → Write framework activation blocked; idempotency mechanism redesigned
Sprint 7 end: duplicate protection still unconfirmed → Write framework deferred; escalate to Platform Lead

**Weekly Check:**
- Idempotency key implementation started: ☐ (Sprint 7)
- ClaimCenter duplicate detection tested: ☐
- Network retry scenario tested: ☐

---

### R10 — Model API Cost Overrun

| Attribute | Value |
|-----------|-------|
| **Status** | OPEN |
| **Category** | Operational / Financial |
| **ADR** | None — operational risk |
| **Sprint Target** | Sprint 3 |
| **Severity** | MEDIUM |
| **Probability** | MEDIUM |

**Description:**
Real AI model calls (Azure OpenAI or Anthropic) incur per-token costs. If claim documents are longer than estimated, retrieval context windows are larger than expected, or governance evaluations require more completions than planned, monthly API costs may exceed the Phase 2 budget allocation. This is particularly relevant during the pilot when claims are processed continuously.

**Mitigation:**
Phase 1 mock AI calls had zero cost. Baseline cost projection can be established from Sprint 3 test runs with real model calls and known token counts.

**Retirement Conditions:**
- [ ] Cost per claim processed estimated from Sprint 3 evaluation runs
- [ ] Monthly cost projection for pilot cohort size confirmed within budget
- [ ] Cost guardrails implemented: max token limits per claim, context window truncation strategy, model tier routing (governance ALLOW → standard model, ESCALATE → senior model)
- [ ] Cost monitoring dashboard operational

**Escalation Path:**
Sprint 3 end: cost per claim exceeds budget target → AI/ML Engineering reviews context window sizes and prompt token counts; implement truncation or chunking strategy
Sprint 4 end: still over budget → Escalate to Platform Lead for budget review or model tier adjustment

**Weekly Check:**
- Real model calls enabled in development: ☐ (Sprint 3)
- Cost per claim estimate computed: ☐
- Budget confirmation received: ☐

---

## Retirement Summary

| Risk | Severity | Sprint Target | Status |
|------|----------|--------------|--------|
| R1 OBO Identity | HIGH | Sprint 1 | OPEN |
| R2 ClaimCenter Spec | HIGH | Sprint 2 | OPEN |
| R3 Golden Dataset | MEDIUM | Sprint 4 | OPEN |
| R4 Write Endpoint Access | HIGH | Sprint 7 | OPEN |
| R5 Prompt Injection | CRITICAL | Sprint 5 | OPEN |
| R6 Hallucination Rate | HIGH | Sprint 5 | OPEN |
| R7 Lower Env Availability | MEDIUM | Sprint 1 | OPEN |
| R8 Adjuster Adoption | HIGH | Sprint 6 | OPEN |
| R9 Write Idempotency | CRITICAL | Sprint 7 | OPEN |
| R10 Cost Overrun | MEDIUM | Sprint 3 | OPEN |

**CRITICAL risks (R5, R9) require explicit sign-off from the Platform Lead before the next phase gate is passed, regardless of retirement condition status.**

---

## How to Update This Matrix

When a retirement condition is met:
1. Check the condition in the table above
2. When all conditions for a risk are met, update the risk status from OPEN → ACTIVE → RETIRED
3. Record the sprint in which retirement was achieved
4. Commit the update to `phase-2-enterprise-integration-foundation` with message: `Risk: retire R{N} — {risk name}`

When an escalation is triggered:
1. Record the escalation date and outcome in a note below the risk block
2. Update the sprint target if the timeline has shifted
3. Notify the escalation path owner via the platform team channel
