# Enterprise AI Workbench — MVP Scope

## Purpose

This document defines the exact scope of the Phase 1 MVP. It is the authoritative reference for what is built, what is deferred, and what architectural principles cannot be compromised.

---

## MVP Vertical Workflow

The MVP proves a single, complete, governed end-to-end workflow:

```
Login
  │
  ▼
Claims Workbench  (search and select a claim)
  │
  ▼
Claim Summary  (AI-generated, governed, source-cited)
  │
  ▼
Scoped Assistant  (multi-turn Q&A grounded in claim + knowledge)
  │
  ▼
Draft Claim Note  (AI-drafted, shown to user for review)
  │
  ▼
Human Approval  (user explicitly approves or rejects)
  │
  ▼
Governed Write  (governance check → write to ClaimCenter if approved)
  │
  ▼
Audit Trail  (immutable record of every decision and action)
```

Every step in this chain is built. No step is skipped or mocked away.

---

## In Scope

### Authentication
- Mock login (username + password → JWT)
- User roles: Adjuster, Supervisor, Auditor
- Session management (JWT expiry, refresh)

### Claims Workbench
- Claim list view (paginated, filterable by status and type)
- Claim detail view (parties, coverages, reserve, status, risk level)
- Claim document list (displayed, not opened in MVP)
- Claim selection triggers session + audit event

### AI Claim Summary
- AI-generated summary of selected claim
- Governance evaluation before generation
- Source citations from knowledge retrieval (RAG)
- Summary displayed with evidence sources visible
- Full summary audit event recorded

### Scoped Conversational Assistant
- Multi-turn conversation scoped to the selected claim
- Each turn: retrieve knowledge → govern → route model → generate → audit
- Conversation history displayed in session
- Evidence sources shown per response
- Governance decision shown per response (ALLOW / DENY / ESCALATE)

### Draft Claim Note
- User requests AI to draft a ClaimCenter note
- Draft displayed for human review before any write
- Governance always returns ESCALATE for draft_note task type (requires human approval)
- User can edit the draft before approving

### Human Approval
- Explicit approve / reject UI action on every draft note
- Approval records who approved and when
- Rejection discards the draft; audit event recorded either way

### Governed Write
- On approval: governance re-evaluated (final check)
- If ALLOW: note written to ClaimCenter (mock in Phase 1)
- If DENY: write blocked, user notified with reason
- Write audit event recorded (success or failure)

### Audit Trail
- Audit log view for the current claim session
- Events: login, claim selected, summary generated, each conversation turn, note drafted, approval decision, write outcome
- Each event shows: timestamp, user, event type, governance decision, model used

### Governance Engine
- Evaluates every AI action before execution
- Returns ALLOW / DENY / ESCALATE with a reason
- Governance decision is always visible to the user
- Draft note task type always triggers ESCALATE (non-configurable in MVP)

### Model Router
- Routes based on task type and claim risk level
- High-risk claims → premium mock model
- Low/medium claims → standard mock model
- All models are mock in Phase 1

### Audit Store
- SQLite-backed in Phase 1
- Append-only (no updates or deletes)
- Queryable by session, claim, user, and event type

---

## Out of Scope (Phase 1 MVP)

| Item | Deferred To |
|------|-------------|
| Real ClaimCenter integration | Phase 2 |
| Enterprise SSO (Azure AD / Okta) | Phase 2 |
| Real AI model calls | Phase 2 |
| Enterprise vector database | Phase 2 |
| Enterprise audit platform (Splunk, Elastic) | Phase 2 |
| PostgreSQL | Phase 2 |
| Policy management UI | Future |
| Model performance analytics | Future |
| Multi-claim workflows | Future |
| Email / notification integration | Future |
| Document viewing / ingestion UI | Future |
| Admin / configuration portal | Future |
| Role management UI | Future |
| Kubernetes / Terraform / CI/CD | Not planned |
| Mobile interface | Not planned |

---

## MVP Success Criteria

The MVP is successful when a user can:

1. Log in with a mock user account and receive a valid session
2. See a list of mock claims and select one
3. Receive a governed, source-cited AI summary of that claim
4. Ask follow-up questions in the scoped assistant and receive governed, grounded responses
5. Request an AI-drafted note and see it displayed for review
6. Approve the note and see it written (to the mock ClaimCenter) with a governance check
7. Reject the note and confirm no write occurs
8. View the complete audit trail for the session showing every governed event

**Governance must be real.** It must demonstrably deny and escalate — not just pass everything through.

**The audit trail must be complete.** Every step above must produce a visible audit record.

**Evidence sources must be cited.** Every AI response must show which knowledge chunks informed it.

---

## Non-Negotiable Architecture Principles

These cannot be compromised regardless of delivery pressure:

1. **No AI model call bypasses governance.** The governance engine is called synchronously before every model invocation. There is no fast path.

2. **No write operation bypasses human approval.** Draft note → human review → human action → governed write. This is enforced in the orchestration layer, not by convention.

3. **Every significant event is audited.** The audit store receives an event for every step in the workflow. Silent failures are not permitted.

4. **The application depends only on interfaces.** Backend routes, services, and domain logic import only `I*` interfaces. Never a concrete adapter class.

5. **Mock adapters are real implementations.** They implement the full interface contract. Replacing them in Phase 2 requires no changes to any consumer.

6. **Governance decisions are always explainable.** Every ALLOW, DENY, and ESCALATE includes a human-readable reason. The UI always displays it.

7. **Prompts are never assembled from raw user input.** User questions are passed as a bounded variable into a controlled prompt template. Injection is prevented by architecture.

---

## Sandbox / Production Replacement Strategy

The MVP is designed so that graduating to Phase 2 (sandbox) requires only:

### Environment Variable Changes

| Variable | Phase 1 | Phase 2 |
|----------|---------|---------|
| `IDENTITY_PROVIDER` | `mock` | `azure_ad` |
| `CLAIMCENTER_ADAPTER` | `mock` | `sandbox` |
| `MODEL_PROVIDER` | `mock` | `anthropic` |
| `AUDIT_STORE` | `sqlite` | `splunk` |
| `KNOWLEDGE_PROVIDER` | `local` | `azure_ai_search` |
| `DATABASE_URL` | `sqlite:///...` | `postgresql://...` |

### New Adapter Implementations

Each new adapter is a new file in the correct `adapters/` subfolder that implements the existing interface. The interface contract does not change. No other file changes.

### Zero Changes Required To

- Frontend
- Backend routes
- Services (model-router, governance, audit, rag, orchestration)
- Domain logic (claims use cases, models)
- Shared contracts
- Governance policies
- Prompt templates

This is the proof that the architecture is production-shaped, not a throwaway prototype.
