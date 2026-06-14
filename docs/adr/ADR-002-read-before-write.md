# ADR-002 — Read-Before-Write Integration Milestone Separation

**Status:** Accepted
**Date:** 2026-06-13
**Phase:** 2 — Enterprise Integration Foundation
**Deciders:** Platform Architecture Team
**Supersedes:** None
**Dependency:** ADR-003 (Identity OBO/Fallback) must be resolved before Write milestone is entered

---

## Context

Phase 2 must connect to real enterprise systems. The two fundamentally different integration categories are:

- **Read integrations** — retrieve claim data, evidence documents, identity context, policy terms, claim history. Failures are recoverable: the workflow shows an error or falls back to a degraded state. A read integration error does not corrupt enterprise data.

- **Write integrations** — submit approved adjuster notes to ClaimCenter, record final audit events to the compliance ledger, update claim status. Failures have consequences: duplicate notes, partial writes, attribution errors, and integrity gaps in the audit record are difficult or impossible to reverse in a regulated system.

The question is whether these two categories should be treated as a single integration milestone or as separate milestones with independent exit criteria.

---

## Decision

**Read integrations and write integrations are separate governed milestones. Real writes are disabled by default until all write-milestone exit criteria are satisfied.**

### Milestone 1 — Live Read Foundation

Live read integrations are enabled in Phase 2 core sprints. The supervisor may invoke read tools against real enterprise systems:

```
read_claim(claim_id)            → ClaimCenter Read API
search_evidence(query, scope)   → Azure Cognitive Search
resolve_identity(session_id)    → Identity Provider (OBO or fallback)
evaluate_policy(context)        → Policy Engine
```

The UX, governance model, and audit trail are unchanged from Phase 1. The only change visible to the adjuster is that claim data, evidence, and AI outputs are derived from real data rather than mock data.

### Milestone 2 — Governed Write Framework

Write integrations are enabled only after all conditions in the write-milestone exit gate are satisfied:

```
submit_note(claim_id, note)     → ClaimCenter Write API  [DISABLED until gate]
```

The `submit_note` tool exists in the tool registry from Sprint 7 onward but is registered with `enabled: false`. Any supervisor attempt to invoke it before the gate is passed raises a `WriteFrameworkNotEnabledError` — recorded as an audit event, surfaced to the adjuster, and never silently ignored.

---

## Write-Milestone Exit Gate

All of the following must be satisfied before the write framework is enabled:

| Condition | Description | Owner |
|-----------|-------------|-------|
| Identity resolved | OBO delegated identity or approved fallback is confirmed (see ADR-003) | IAM / Platform |
| Idempotency key | Every write request carries a platform-generated idempotency key; ClaimCenter duplicate detection confirmed | Platform Engineering |
| Reconciliation baseline | Read-back after write is implemented and tested — submitted note is retrieved and verified against what was sent | Platform Engineering |
| Approval record integrity | Approval record is verified present and unexpired before every write invocation — not a UI check, a service-layer check | Platform Engineering |
| ClaimCenter write contract | Specification-backed write contract is validated against ClaimCenter lower environment (see ADR-004) | Integration Engineering |
| Security review | Write path reviewed by security: token handling, injection surface on note content, rate limiting | Security |
| Compliance sign-off | Compliance has reviewed the audit trail for write events and approved the attribution model | Compliance |
| IAM approval | IAM / network / firewall access to ClaimCenter write endpoint approved for the deployment environment | IAM / Infrastructure |
| Rollback procedure | Write rollback procedure is documented, tested, and approved — what happens if a note is submitted in error | Operations |

---

## Rationale

### Risk asymmetry

The risk profiles of read and write integrations are fundamentally different:

| Dimension | Read Failure | Write Failure |
|-----------|-------------|---------------|
| Data impact | None — source system unchanged | Potential duplicate, partial, or incorrectly attributed note in ClaimCenter |
| Recoverability | Immediate — retry or degrade gracefully | Difficult — requires ClaimCenter administrator action to correct or void |
| Regulatory impact | None | Potentially significant — incorrect note in a claim record is a compliance event |
| Adjuster impact | Degraded UX — AI falls back to reduced quality | Adjuster may have signed an approval for a note that was never written, or a note may be written without a complete approval record |
| Audit impact | Read failure recorded as an error event | Write failure recorded as an error event, but a partial write may produce a note in ClaimCenter without a corresponding platform audit record |

Treating read and write as a single milestone means the write framework goes live at the same time as live claim data — before identity, idempotency, reconciliation, and compliance approval are confirmed. This is the primary risk mitigation the separation provides.

### Adjuster experience is unchanged

During Milestone 1, the adjuster sees the same approval screen as in Phase 1. The approval is recorded as a platform audit event. The note is held in the platform's `DRAFT` state. When the adjuster clicks "Submit", the platform records the intent and displays "Ready for Write-back" — identical to Phase 1 behaviour.

The transition from "Ready for Write-back" to "Written to ClaimCenter" is a write-layer change, not a UX change. The adjuster workflow, the approval checklist, and the audit trail are unchanged at Milestone 2 entry. Only the final step — the `submit_note` tool invocation — becomes active.

### It is safer to defer write than to rush it

A write integration that goes wrong in a production ClaimCenter is a regulated event. A write integration that is deferred for one additional sprint while idempotency and reconciliation are confirmed is a scheduling decision. The asymmetry is obvious: the cost of deferral is a sprint; the cost of a write failure in production is a compliance incident.

---

## Consequences

**Positive:**
- Read integrations can be developed, tested, and validated independently of write complexity
- Adjuster training can begin on live read data before write is enabled
- Identity, idempotency, reconciliation, and compliance can be validated against a real write path in the lower environment before production
- If the write gate cannot be satisfied in Phase 2 (e.g., OBO is delayed), Phase 2 ships with live reads and write remains deferred — the platform is still usable and valuable

**Negative:**
- Write-ready adjuster workflows are in "Ready for Write-back" state throughout Milestone 1 — adjusters must be informed that write-back is deferred and notes should be submitted via the existing manual process in parallel
- The dual-workflow (platform draft + manual submission) during Milestone 1 creates a reconciliation burden that operations must manage
- Platform audit trail for Milestone 1 includes approved notes that were never written to ClaimCenter — this gap must be disclosed in the compliance review

**Mitigation for negative consequences:**
- Adjuster onboarding materials clearly describe Milestone 1 as "live AI, manual write" mode
- Operations defines a Milestone 1 reconciliation process for approved platform drafts
- Compliance acknowledges the draft-not-written state in the audit trail design review

---

## Review Trigger

This decision should be reviewed if:
- ClaimCenter lower environment write contract is confirmed and all write gate conditions are satisfied ahead of the sprint plan
- A regulatory requirement emerges that requires write and read to be activated simultaneously
- OBO identity is confirmed earlier than expected, removing the primary write-gate blocker
