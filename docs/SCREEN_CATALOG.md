# Screen Catalog — Enterprise AI Workbench

**Version:** Phase 1 — Reference Implementation (v1.0.0)
**Live Demo:** https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench

This catalog documents all ten screens in the Phase 1 application. Each screen entry covers purpose, primary user, business value, inputs, outputs, AI capabilities, governance controls, navigation, and Phase 2 enhancements.

---

## Screen 1 — Enterprise Login

**Route:** `/login`
**Status:** Phase 1 — Mock (no real authentication)

### Purpose
Entry point to the platform. Establishes user identity and initiates the governed session. In Phase 1, authentication is mocked — the user proceeds directly into the workbench as a pre-authenticated adjuster.

### Primary User
Claims adjuster, claims supervisor, audit reviewer

### Business Value
- Establishes the actor identity that appears on every subsequent audit event
- Enforces access control — only authenticated users can initiate AI-assisted workflows
- Provides the session context used by the governance engine for policy evaluation

### Inputs
- Username / employee ID (Phase 1: mock)
- Password / SSO token (Phase 1: mock)

### Outputs
- Authenticated session with user identity, role, and permissions
- `session.established` audit event recorded

### AI Capabilities
None — login is a pure identity and access control function.

### Governance Controls
- Identity verification before any AI action is permitted
- Session context passed to the governance engine on all subsequent requests
- Failed authentication attempts recorded (Phase 2)

### Navigation
- On successful authentication → Executive Dashboard (`/dashboard`)

### Phase 2 Enhancements
- Enterprise SSO (Okta, Azure AD, or internal identity provider)
- Role-based access control (adjuster vs. supervisor vs. read-only auditor)
- MFA enforcement for high-risk claim categories
- Session timeout and re-authentication for write operations

---

## Screen 2 — Executive Dashboard

**Route:** `/dashboard`
**Status:** Phase 1 — Complete (static mock analytics)

### Purpose
Leadership-facing operations overview. Surfaces AI performance KPIs, model utilization, governance distribution, use case volume, execution timeline, and platform health in a single view. Designed for the Chief Claims Officer, Head of Digital, and divisional leadership — not the adjuster.

### Primary User
Chief Claims Officer, VP Claims Operations, Head of AI/Digital, IT Director

### Business Value
- Single view of AI governance health — ALLOW / DENY / ESCALATE distribution
- Operational efficiency metrics — processing time, human approval rate, cost per request
- Model utilization and cost transparency — which models are being used and at what cost
- Platform health — all services operational, zero policy violations

### Inputs
- AI operations telemetry (Phase 1: static mock data)
- Governance engine outcome distribution (Phase 1: static)
- Model utilization metrics (Phase 1: static)

### Outputs
- KPI cards: Claims AI Assisted (2,481 MTD), Human Approval Rate (96%), Governance Allow Rate (99.2%), Avg AI Confidence (93%), Avg Processing Time (6.4 min), Est. Monthly Savings ($148K)
- Model utilization bars: GPT-4.1-mini (52%), Claude Sonnet (33%), Gemini Flash (15%)
- Governance distribution: ALLOW (96%), ESCALATE (3%), DENY (1%)
- Top AI use cases by request volume
- Today's execution timeline for the most recent completed workflow
- Enterprise platform health: all services operational, zero policy violations

### AI Capabilities
None — dashboard is a reporting surface, not an AI execution surface.

### Governance Controls
- Policy Violations counter: 0 (governance engine prevented all non-compliant actions)
- Governance Allow Rate displayed prominently to confirm policy engine health
- All metrics represent governance-evaluated AI actions only

### Navigation
- Sidebar → Claims Workbench (`/home`)
- Sidebar → Audit Trail (via individual claim)

### Phase 2 Enhancements
- Real-time telemetry from PostgreSQL analytics store
- Drill-down from governance outcomes to individual claim audit records
- Cost reporting against actual Azure OpenAI billing
- Trend charts (7-day, 30-day, MTD)
- Anomaly detection on governance DENY rate spikes
- Export to PDF / Excel for board reporting

---

## Screen 3 — Claims Workbench

**Route:** `/home` and `/claims`
**Status:** Phase 1 — Complete

### Purpose
The adjuster's primary working view. Lists all claims assigned to the current user with status, priority, claim type, and AI readiness indicators. The starting point for every claim workflow.

### Primary User
Claims adjuster

### Business Value
- Prioritised claim queue — adjusters work the right claims at the right time
- AI readiness indicator — adjuster knows at a glance whether the AI has prepared analysis for a claim
- Status transparency — claim state visible without opening the claim detail

### Inputs
- Claim list from `IClaimRepository` (Phase 1: `MockClaimRepository`)
- Current user session for filtering to assigned claims

### Outputs
- Paginated list of claims with: claim number, claimant name, claim type, status, date opened, AI readiness indicator

### AI Capabilities
None on this screen — AI actions begin on the claim detail screen.

### Governance Controls
- Only claims accessible to the authenticated adjuster are displayed (Phase 2: enforced by ClaimCenter access control)
- Governance status indicator shows whether the claim's current AI session is within policy

### Navigation
- Click any claim → Claim Detail (and from there, all AI workflow screens)
- Sidebar → Executive Dashboard (`/dashboard`)

### Phase 2 Enhancements
- Live claim list from ClaimCenter API
- Filter and sort by claim type, status, priority, date, AI confidence threshold
- Assignment and routing — supervisor can reassign claims from this view
- AI triage scoring — claims ranked by AI-assessed complexity and risk
- Bulk actions — mark multiple claims for review or escalation

---

## Screen 4 — AI Claim Summary

**Route:** `/claims/:id/summary`
**Status:** Phase 1 — Complete

### Purpose
The primary AI-assisted work product for each claim. Presents an evidence-grounded, confidence-scored summary of the claim — coverage position, key facts, liability assessment, and recommended action — generated from the retrieved evidence documents.

### Primary User
Claims adjuster

### Business Value
- Reduces time-to-first-review from hours to seconds
- Every conclusion is grounded in a cited evidence source — not hallucinated
- Confidence score gives the adjuster an immediate signal of AI certainty
- Recommended action provides a clear starting point for the adjuster's decision

### Inputs
- Claim record from `IClaimRepository`
- Retrieved evidence documents from `IKnowledgeProvider`
- Governance evaluation result from `IGovernanceEngine`
- Model selection from `IModelRouter`
- AI generation from `IModelProvider`

### Outputs
- Claim summary with: coverage position, key facts, liability assessment, recommended action
- Confidence score (0–100%)
- Evidence citations with relevance scores
- Governance status badge (ALLOW / DENY / ESCALATE)
- Audit event: `ai.summary.generated`

### AI Capabilities
- Evidence retrieval (RAG): retrieves and ranks relevant documents for this claim
- Claim summarisation: generates structured summary from retrieved evidence
- Confidence scoring: produces a confidence estimate over the summary
- Model routing: selects appropriate model for summarisation task

### Governance Controls
- Governance engine evaluates the summarisation request before the model is invoked
- If governance returns DENY, the summary is not generated and the reason is displayed
- If governance returns ESCALATE, the request is routed to a supervisor before proceeding
- Policy set version recorded on the audit event

### Navigation
- Tab bar: Summary | Assistant | Evidence | Draft Note | Approval | Audit
- → AI Claim Assistant (`/claims/:id/conversation`)
- → Evidence & Explainability (`/claims/:id/evidence`)

### Phase 2 Enhancements
- Live AI generation from Azure OpenAI (GPT-4.1 or equivalent)
- Real RAG from Azure Cognitive Search over claim document corpus
- Summary editing — adjuster can annotate or correct AI summary before proceeding
- Summary versioning — track changes if the adjuster modifies the AI output
- Comparative analysis — AI highlights how this claim differs from similar historical claims

---

## Screen 5 — AI Claim Assistant

**Route:** `/claims/:id/conversation`
**Status:** Phase 1 — Complete

### Purpose
Context-scoped conversational AI for the adjuster. The adjuster can ask any question about the current claim, and the AI responds based exclusively on the retrieved evidence for that claim. Cross-claim queries and out-of-scope questions are refused by the governance engine.

### Primary User
Claims adjuster

### Business Value
- Interactive claim analysis without leaving the claim context
- Adjuster can probe specific aspects of the claim — coverage gaps, liability ambiguity, precedent
- Every question-answer pair is governed and audited
- AI cannot hallucinate beyond the retrieved evidence context

### Inputs
- User message (adjuster's question)
- Claim context and evidence from `IKnowledgeProvider`
- Session ID for conversation continuity
- Governance evaluation per turn from `IGovernanceEngine`

### Outputs
- AI response grounded in claim evidence
- Evidence citations supporting the response
- Per-turn governance evaluation (ALLOW / DENY / ESCALATE)
- Audit event: `conversation.turn` and `governance.evaluated` per turn

### AI Capabilities
- Contextual question answering: responds to adjuster questions using retrieved claim evidence
- Context isolation: AI prompt is scoped exclusively to this claim's evidence — no other claim data
- Conversation memory: maintains prior turns within the session
- Out-of-scope detection: governance engine refuses questions outside the claim context

### Governance Controls
- **Per-turn governance**: every message is evaluated by the governance engine before the AI responds
- **Context isolation**: adjuster cannot extract information from other claims via this interface
- **Scope enforcement**: out-of-scope questions (e.g. "what is the weather today") are refused with a governance DENY and reason
- Every turn recorded as a governance-attributed audit event

### Navigation
- Tab bar: Summary | Assistant | Evidence | Draft Note | Approval | Audit
- → Draft Note (`/claims/:id/draft-note`)

### Phase 2 Enhancements
- Live conversation via Azure OpenAI with streaming responses
- Real-time governance evaluation with sub-100ms latency
- Supervisor visibility — supervisor can view conversation history for escalated claims
- Conversation export — adjuster can export the conversation as supporting documentation
- Follow-up question suggestions based on the AI's response

---

## Screen 6 — Evidence & Explainability

**Route:** `/claims/:id/evidence`
**Status:** Phase 1 — Complete

### Purpose
Transparency layer showing the adjuster exactly which documents the AI used to produce its outputs, ranked by relevance and confidence. This is the explainability screen — every AI conclusion is traceable to a specific source.

### Primary User
Claims adjuster, claims supervisor, audit reviewer, legal

### Business Value
- Regulatorily defensible — every AI output is traceable to a specific document
- Adjuster can verify the AI used the right evidence before approving the draft note
- Legal can retrieve the evidence record if a claim decision is challenged
- Reduces the risk of AI acting on irrelevant or outdated documents

### Inputs
- Evidence retrieval results from `IKnowledgeProvider`
- Relevance scores and ranking from the retrieval model

### Outputs
- Ranked list of evidence sources: document type, content excerpt, relevance score, retrieval timestamp
- Source type indicators: police report, repair estimate, claimant statement, medical report, photo evidence, policy document
- Evidence used in AI summary vs. evidence retrieved but not used

### AI Capabilities
- Evidence ranking: documents are ranked by semantic relevance to the claim
- Source attribution: each AI output is linked to the evidence that produced it
- Evidence sufficiency scoring: AI indicates when retrieved evidence is insufficient to produce a high-confidence output

### Governance Controls
- Evidence scope is restricted to documents authorised for this claim
- Evidence retrieval is logged as an audit event with document IDs and retrieval timestamp
- Adjuster cannot retrieve evidence from other claims through this screen

### Navigation
- Tab bar: Summary | Assistant | Evidence | Draft Note | Approval | Audit
- → AI Claim Summary (`/claims/:id/summary`)
- → Draft Note (`/claims/:id/draft-note`)

### Phase 2 Enhancements
- Live document retrieval from Azure Cognitive Search
- Document preview — click any evidence source to view the full document
- Evidence gap analysis — AI flags what documents are missing or would improve confidence
- Evidence provenance — full chain of custody from original document ingestion to retrieval

---

## Screen 7 — AI Draft Claim Note

**Route:** `/claims/:id/draft-note`
**Status:** Phase 1 — Complete

### Purpose
The AI generates a structured adjuster note based on the claim summary and evidence. The note is held in DRAFT status — it cannot be submitted to ClaimCenter until the adjuster reviews it and completes the formal approval process on the next screen.

### Primary User
Claims adjuster

### Business Value
- Eliminates adjuster time spent writing routine claim notes — AI drafts, adjuster approves
- Consistent note format across all claims processed through the platform
- DRAFT status makes clear that the note has not been approved or written to ClaimCenter
- Adjuster retains full authority to edit or reject the draft

### Inputs
- AI claim summary
- Retrieved evidence
- Draft note template (from `shared/prompts/`)
- Governance evaluation from `IGovernanceEngine`

### Outputs
- Structured draft note with: claim overview, coverage assessment, key findings, recommended action, adjuster attribution
- DRAFT watermark — note is clearly not yet approved
- Confidence indicator
- Audit event: `draft.note.generated`

### AI Capabilities
- Note generation: produces a structured adjuster note in standard claims format
- Template adherence: note conforms to the organisation's note format (Phase 2: configurable)
- Evidence grounding: note references specific evidence items, not general conclusions

### Governance Controls
- Note generation request evaluated by governance engine before the model is invoked
- DRAFT status enforced — no mechanism exists to submit the note to ClaimCenter without approval
- Note content is stored in the audit record alongside the approval decision

### Navigation
- Tab bar: Summary | Assistant | Evidence | Draft Note | Approval | Audit
- → Governed Approval (`/claims/:id/approval`)

### Phase 2 Enhancements
- Adjuster inline editing of the draft note before submission
- Multiple draft note templates (liability, property, medical, auto)
- AI-suggested edits — AI flags sections of the draft that may need adjuster verification
- Draft versioning — track all edits from AI draft to final approved note

---

## Screen 8 — Governed Approval

**Route:** `/claims/:id/approval`
**Status:** Phase 1 — Complete

### Purpose
The human approval gate. The adjuster reviews the AI draft note, completes a structured checklist confirming they have reviewed the evidence and accept responsibility for the decision, and explicitly commits the approval. This is the architectural enforcement of human authority over AI.

### Primary User
Claims adjuster (submitter), claims supervisor (reviewer for escalated claims)

### Business Value
- **Human authority is enforced by architecture** — the AI cannot write to ClaimCenter without this approval
- Structured checklist ensures adjuster has verified: AI summary reviewed, evidence checked, policy coverage confirmed, note content accurate
- Explicit commitment — the adjuster signs the approval with their user identity
- Approval record is permanent — the audit trail records who approved, when, and what checklist items were confirmed

### Inputs
- AI draft note
- Adjuster acknowledgement checklist
- Adjuster notes / comments (optional)
- Approval decision (Approve / Reject)
- Current user identity from session

### Outputs
- Approval record: approver identity, timestamp, checklist confirmation, decision
- Audit event: `approval.submitted` with decision, actor, and checklist state
- If Approved → write-back proceeds (Phase 2: to ClaimCenter)
- If Rejected → workflow returns to draft stage; rejection reason recorded

### AI Capabilities
None — the approval screen is a human decision surface. AI has no role in the approval decision.

### Governance Controls
- Approval cannot be submitted without all checklist items confirmed
- Approver identity is verified against the session — cannot approve on behalf of another user
- Approval record is immutable once submitted
- Rejection reasons are recorded and surfaced in the audit trail

### Navigation
- On Approve → Write Progress / Write Complete
- On Reject → returns to Draft Note
- Tab bar: Summary | Assistant | Evidence | Draft Note | Approval | Audit

### Phase 2 Enhancements
- Supervisor approval for high-value or escalated claims (dual approval)
- Electronic signature capture
- Approval delegation — supervisor can approve on behalf of an absent adjuster with an explicit override record
- SLA enforcement — approval must be completed within a configurable window or the claim is escalated

---

## Screen 9 — Write Progress / Write Complete

**Route:** Post-approval confirmation state
**Status:** Phase 1 — Complete (mock write-back, shows Ready for Write-back state)

### Purpose
Confirms that the adjuster's approval has been recorded and the note is ready for write-back to ClaimCenter. In Phase 1, the write-back is simulated — the system records the intent and flags the note as approved and write-ready. In Phase 2, the actual API call to ClaimCenter is made here.

### Primary User
Claims adjuster

### Business Value
- Clear confirmation that the approval was recorded — no ambiguity about whether the action completed
- In Phase 2: confirmation that the note was successfully written to ClaimCenter
- Write-back audit event provides the closing record for the governance chain

### Inputs
- Approval record from the Governed Approval screen
- ClaimCenter write-back result (Phase 2)

### Outputs
- Confirmation: "Note approved and ready for write-back" (Phase 1)
- Confirmation: "Note written to ClaimCenter — reference [ID]" (Phase 2)
- Audit event: `claimcenter.note.written` (description: "The approved draft note is ready for governed write-back")

### AI Capabilities
None — write-back is a system action following human approval.

### Governance Controls
- Write-back only proceeds after a valid approval record exists
- Write-back attempt and outcome recorded as audit events
- Failed write-back (Phase 2: API error) recorded with error details — no silent failures

### Navigation
- → Audit Trail (`/claims/:id/audit`)
- → Claims Workbench (`/home`)

### Phase 2 Enhancements
- Real ClaimCenter API write via `IClaimNoteWriter` adapter
- Retry logic with exponential backoff for transient API failures
- Write-back receipt — ClaimCenter-issued reference ID stored in the audit record
- Async write with progress indicator for large claims

---

## Screen 10 — Audit & Trace Explorer

**Route:** `/claims/:id/audit`
**Status:** Phase 1 — Complete

### Purpose
The compliance and traceability record for every AI action taken on a claim. An eleven-event immutable timeline showing — in chronological order — every significant action taken by any actor (USER, AI, GOVERNANCE, SYSTEM) during the claim workflow. Each event is expandable to show full metadata.

### Primary User
Claims adjuster, claims supervisor, compliance officer, auditor, legal, IT operations

### Business Value
- **Regulatory compliance**: complete, tamper-proof record of every AI action and human decision
- **Dispute resolution**: if a claim decision is challenged, the audit record shows exactly what the AI recommended, what evidence was used, and what the adjuster approved
- **AI accountability**: every AI output is attributed to a specific model, governance outcome, and confidence score
- **Performance analysis**: latency and confidence data supports model quality assessment
- **Internal audit**: compliance and legal can review the full governance chain for any claim without accessing the claim system directly

### Inputs
- Audit event stream from `IAuditStore` (Phase 1: in-memory, 11 events per claim)

### Outputs
Three-panel layout:

**Left panel — Claim context**
- Claim ID, type, status
- Session information
- Immutable record notice
- Governance Active badge

**Centre panel — Event timeline (expandable)**
Each event shows:
- Timestamp (UTC)
- Event type label
- Actor type (USER / AI / GOVERNANCE / SYSTEM) with colour coding
- Status badge (INFO / SUCCESS / ALLOW / DENY / ESCALATE)
- On expand: description, evidence count, confidence score, policy set, routing reason, actor name, latency

**Right panel — Summary metrics and execution path**
- 9 audit summary metrics (total events, AI events, governance events, etc.)
- 10-step execution path with completion indicators

### AI Capabilities
None — this screen displays the record of AI actions. No AI executes on this screen.

### Governance Controls
- Audit events are append-only — no event can be modified or deleted
- Each event records the policy set version under which it was evaluated
- Actor attribution on every event — USER, AI, GOVERNANCE, or SYSTEM
- Confidence and latency recorded on all AI and governance events

### The 11 Audit Events (Phase 1)

| # | Event Type | Actor | Status | Description |
|---|-----------|-------|--------|-------------|
| 1 | `session.established` | SYSTEM | INFO | User session established with identity and permissions |
| 2 | `claim.accessed` | USER | INFO | Adjuster opened the claim record |
| 3 | `evidence.retrieved` | AI | SUCCESS | Evidence retrieved and ranked from knowledge store |
| 4 | `governance.evaluated` | GOVERNANCE | ALLOW | Policy engine evaluated the summarisation request |
| 5 | `model.routed` | AI | SUCCESS | Model router selected the appropriate AI model |
| 6 | `ai.summary.generated` | AI | SUCCESS | AI claim summary generated with confidence score |
| 7 | `conversation.turn` | AI | SUCCESS | Adjuster question processed and response generated |
| 8 | `governance.evaluated` | GOVERNANCE | ALLOW | Per-turn governance check on conversation request |
| 9 | `draft.note.generated` | AI | SUCCESS | Draft adjuster note generated from summary and evidence |
| 10 | `approval.submitted` | USER | SUCCESS | Adjuster reviewed and approved the draft note |
| 11 | `claimcenter.note.written` | SYSTEM | SUCCESS | Approved note ready for governed write-back |

### Navigation
- Tab bar: Summary | Assistant | Evidence | Draft Note | Approval | Audit
- → Claims Workbench (`/home`)
- → Executive Dashboard (`/dashboard`)

### Phase 2 Enhancements
- Real audit events from PostgreSQL with write-only audit user
- Full-text search across audit events for a claim
- Cross-claim audit reporting — compliance officer can search all audit events by date range, actor, or governance outcome
- Cryptographic integrity proofs — hash chain on audit events for tamper detection
- Export to PDF / JSON for regulatory submission
- Alert on anomalous governance DENY patterns
