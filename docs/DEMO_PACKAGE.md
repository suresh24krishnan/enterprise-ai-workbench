# Demo Package — Enterprise AI Workbench

**Live Demo:** https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench
**Version:** Phase 1 — Reference Implementation (v1.0.0)

---

## Before You Demo

- Open the live demo URL in a browser and confirm the Space is running (green status).
- The demo loads with mock data — no login credentials required in Phase 1.
- All data is fictional. Claim numbers, adjuster names, and dollar amounts are illustrative.
- The governance engine, audit trail, and approval gate are fully functional — they are not mocked UI elements.

---

## 5-Minute Executive Demo

**Audience:** C-suite, divisional VP, board observer
**Goal:** Establish that this is a governance-first AI platform, not a chatbot, and that it is already deployed and running.

### Minute 1 — Open with the business problem

> "Every AI pilot we see in claims processing runs into the same three questions from legal and compliance: who authorised this action, why did the AI produce this specific output, and what stopped it from acting on bad data. Most AI tools cannot answer any of them. This platform answers all three — by design."

**Navigate to:** Executive Dashboard

> "This is the AI Operations Dashboard. It shows everything leadership needs to see about how AI is performing across the claims division — in real time. Notice: 99.2% governance allow rate, 96% human approval rate, zero policy violations this month."

**Point to:** Governance Distribution card

> "The governance engine evaluated every single AI request. 96% were allowed automatically. 3% were escalated to a human reviewer. 1% were denied outright. Every outcome is recorded."

### Minute 2 — Open a claim

**Navigate to:** Claims Workbench → click any claim

> "Here is the claims workbench. The adjuster selects a claim. The system has already retrieved the relevant evidence and is ready to route to the appropriate AI model."

**Navigate to:** AI Claim Summary

> "This is the AI-generated claim summary. Notice the confidence score — 94%. Notice the evidence citations — the AI is not generating from training data, it is reasoning over the actual claim documents: the police report, the repair estimate, the claimant statement. Every piece of evidence is ranked and cited."

### Minute 3 — Show the governance gate

**Navigate to:** AI Claim Assistant, type a question

> "The adjuster can ask the AI anything about this claim. Watch what happens when the AI processes a question."

*Wait for response.*

> "Before that response was returned, the governance engine evaluated the request against the policy set, recorded the evaluation, and produced an ALLOW decision. The AI did not act until governance cleared it. That evaluation is permanently recorded in the audit trail."

### Minute 4 — Show the approval gate

**Navigate to:** AI Draft Claim Note → Governed Approval

> "The AI has drafted an adjuster note. It is in DRAFT status. The adjuster must review it, complete a structured checklist, and explicitly commit to the decision. The AI cannot write anything to any system without that approval. Human authority is enforced by architecture, not by policy."

### Minute 5 — Show the audit trail

**Navigate to:** Audit Trail

> "Every action taken in this workflow — the session establishment, the evidence retrieval, the governance evaluation, the model selection, the AI output, the human approval, the write-back readiness — is recorded here with a timestamp, actor type, status, and outcome. This is your compliance record. It is append-only. Nothing can be altered after the fact."

**Close:**

> "This is not a prototype. It is running right now. The architecture is built to production standards. In Phase 2, we replace the mock adapters with your ClaimCenter API and identity provider. The governance model, the audit trail, and the human approval gate stay exactly as you see them today."

---

## 7-Minute Leadership Demo

**Audience:** Operations VP, Chief Claims Officer, Head of Digital, IT Director
**Goal:** Show the full workflow, explain the governance model, and surface the Phase 2 path.

### Minute 1 — Executive Dashboard (2 min)

Open the Executive Dashboard. Walk through each section:

**KPI row:**
> "2,481 claims AI-assisted this month. 96% of those went through human approval. The governance engine allowed 99.2% of AI requests automatically. Average confidence score across all AI tasks is 93%. Average end-to-end processing time is 6.4 minutes."

**Model utilization:**
> "The platform routes each AI task to the appropriate model based on task type, risk level, and cost. GPT-4.1-mini handles 52% of requests — routine summarisation. Claude Sonnet handles complex reasoning at 33%. Gemini Flash handles latency-sensitive tasks at 15%. The adjuster never chooses a model. The router does."

**Governance distribution:**
> "This is the one slide leadership needs to see. Every AI request is evaluated. 96% ALLOW, 3% ESCALATE, 1% DENY. Zero policy violations. The governance engine is not a checkbox — it is an enforcement layer that runs before every AI action."

### Minute 2 — Claims Workbench (1 min)

Navigate to Claims Workbench.

> "The adjuster's starting point. The claim list shows status, priority, and AI readiness indicators. The adjuster selects a claim and the platform loads the full context — claim data, evidence, prior conversation history, and current governance status."

### Minute 3 — AI Claim Summary + Evidence (2 min)

Navigate to AI Claim Summary.

> "The AI summary is generated from the actual claim documents — not from a general model with no context. The system retrieves relevant evidence, ranks it by confidence and relevance, and grounds every statement in a cited source. The adjuster can see exactly which document produced each conclusion."

Navigate to Evidence & Explainability.

> "This is the evidence panel. Every source is ranked. Every citation is traceable. If the AI says 'estimated repair cost: $12,400' — the source is the repair estimate document, confidence 0.91. This is the explainability layer. It is what legal needs when a claim decision is challenged."

### Minute 4 — Governed Assistant (1 min)

Navigate to AI Claim Assistant.

> "The adjuster can ask the AI anything about this claim. The AI is scoped exclusively to the evidence for this claim — it cannot access other claims, it cannot use general internet knowledge, it cannot hallucinate beyond the retrieved context. Each question triggers a governance evaluation before the AI responds."

### Minutes 5–6 — Draft Note + Approval (2 min)

Navigate to AI Draft Claim Note.

> "The AI drafts the adjuster note. It is flagged as DRAFT. The adjuster reads it, edits if needed, then moves to the approval gate."

Navigate to Governed Approval.

> "The approval screen requires the adjuster to complete a structured checklist and explicitly commit to the decision. They are confirming that they have reviewed the AI output, the evidence, and the claim data — and they are taking personal responsibility for the decision. The AI cannot write to ClaimCenter until this approval is recorded."

### Minute 7 — Audit Trail (1 min)

Navigate to Audit Trail.

> "Eleven events recorded for this claim workflow. Each event has an actor type — USER, AI, GOVERNANCE, or SYSTEM. Each has a status, a latency, and a confidence score where applicable. The timeline is append-only. It cannot be edited. This is your regulatory audit record, produced automatically, for every claim the AI touches."

**Phase 2 transition:**

> "Everything you have seen today runs on mock adapters. In Phase 2, we connect to your real systems — ClaimCenter sandbox, your identity provider, your model gateway. The governance model, the audit trail, and the approval gate are already built. We are not redesigning anything. We are wiring real adapters into an architecture that is already production-ready."

---

## 10-Minute Technical Walkthrough

**Audience:** Engineering lead, solution architect, senior developer, enterprise architect
**Goal:** Demonstrate the architecture quality, the hexagonal design, and the Phase 2 adapter swap strategy.

### Section 1 — Architecture Overview (2 min)

Navigate to Executive Dashboard while narrating the architecture:

> "The platform is built on Hexagonal Architecture — Ports & Adapters. The business domain — claims — has no dependency on infrastructure. Every external system is accessed through a typed interface. `IClaimRepository`, `IModelProvider`, `IGovernanceEngine`, `IAuditStore` — all interfaces, no concrete implementations in the business layer."

> "In Phase 1, every interface is satisfied by a mock adapter. The only file that imports concrete implementations is `dependencies.py`. That is intentional. Swapping mock for real in Phase 2 means implementing the interface and updating the wiring in `dependencies.py`. Nothing else changes."

### Section 2 — Governance Engine (2 min)

Navigate to AI Claim Summary. Show the governance badge on the page.

> "The governance engine is not middleware — it is a service called explicitly before every AI action. The service evaluates the request against the active policy set — `mvp_policy_set v1.0` in Phase 1 — and returns ALLOW, DENY, or ESCALATE. The AI model is never invoked until the governance engine returns ALLOW."

Navigate to Audit Trail, expand the `governance.evaluated` event.

> "The governance evaluation is recorded as an audit event: the policy set name, the outcome, the latency, and the actor. The record is immutable. In Phase 2, the policy engine is replaced with a real rule-based engine backed by PostgreSQL. The audit interface is unchanged — only the adapter changes."

### Section 3 — Model Router (1 min)

> "The model router selects the appropriate AI model before execution. The routing logic considers task type — summarisation versus reasoning versus analysis — risk level derived from governance evaluation, and cost constraints. In Phase 1, the router produces deterministic mock selections. In Phase 2, it routes to real models through an enterprise model gateway."

### Section 4 — RAG & Evidence (2 min)

Navigate to Evidence & Explainability.

> "Evidence retrieval uses a `IKnowledgeProvider` interface. In Phase 1, the mock provider returns static evidence documents ranked by relevance score. In Phase 2, this is replaced with an Azure Cognitive Search adapter. The evidence schema — document ID, content, score, source type — is already defined. The Phase 2 adapter returns the same schema from a real vector store."

> "The AI model receives only the retrieved evidence in its context window, not the full claim history or any data from other claims. Context isolation is enforced by the orchestration service, not by the model."

### Section 5 — Audit Trail (1 min)

Navigate to Audit Trail.

> "The audit store interface is `IAuditStore` — a single append-only method. Events are never updated or deleted. In Phase 1, the store is in-memory. In Phase 2, it writes to PostgreSQL with a write-only audit user. The interface is identical. The event schema — event_id, event_type, actor_type, actor_name, status, timestamp, latency, confidence, description — is defined in Phase 1 and will not change."

### Section 6 — Deployment & Docker (1 min)

> "The full application runs in a single Docker container: nginx on port 7860 serves the React SPA and proxies `/api/*` to uvicorn on internal port 8000. Supervisord manages both processes with auto-restart. The container is deployed to Hugging Face Docker Spaces. The same Dockerfile deploys to Azure Container Apps with a single environment variable change."

> "The frontend is built with Vite. The API base URL is set at build time via environment variable. In local development, it points to localhost. In Docker, it is set to empty string so all API calls are relative — they go through the nginx proxy."

### Section 7 — Phase 2 Adapter Swap (1 min)

> "Here is what Phase 2 looks like in code terms. We create `ClaimCenterSandboxRepository` implementing `IClaimRepository`. We create `SSOIdentityProvider` implementing `IIdentityProvider`. We create `AzureOpenAIProvider` implementing `IModelProvider`. We add three lines to `dependencies.py` to wire the new adapters. We run `docker-compose up`. Every page, every API endpoint, every governance control, every audit event — unchanged."

---

## Business Outcomes

| Outcome | How the Platform Delivers It |
|---------|------------------------------|
| Reduced claim processing time | AI-assisted summary and note generation eliminates manual research and writing |
| Improved decision consistency | Governance engine enforces the same policy rules on every claim, every time |
| Regulatory defensibility | Immutable audit trail with actor, status, latency, and evidence citations on every AI action |
| Human authority preserved | No AI output reaches ClaimCenter without explicit adjuster approval |
| Explainable AI | Every conclusion is grounded in cited, ranked evidence — no black-box outputs |
| Reduced model costs | Intelligent routing sends each task to the lowest-cost model that meets the quality threshold |
| Accelerated Phase 2 | Architecture is complete — Phase 2 is adapter implementation, not platform design |

---

## Technical Differentiators

| Differentiator | Detail |
|----------------|--------|
| Hexagonal Architecture | Business logic has zero dependency on infrastructure — adapters are swappable without touching business rules |
| Governance-first design | Policy engine runs before every AI action — governance is enforced, not advisory |
| Context isolation | AI assistant is scoped to the specific claim's evidence — cross-claim data leakage is architecturally prevented |
| Immutable audit trail | Append-only event log with actor type, status, latency, confidence — cannot be edited after the fact |
| Model routing | Task-appropriate model selection before execution — cost and quality optimised per task type |
| Interface-defined contracts | Every adapter implements a typed interface — Phase 2 is a contract fulfilment, not a redesign |
| TypeScript strict mode | Frontend uses strict TypeScript throughout — runtime type errors are caught at compile time |
| Single entrypoint for DI | `dependencies.py` is the only wiring point — all other code depends on interfaces |

---

## Governance Differentiators

| Differentiator | Detail |
|----------------|--------|
| Pre-execution governance | Every AI action evaluated before the model is invoked — governance cannot be bypassed |
| ALLOW / DENY / ESCALATE | Three-outcome policy evaluation — not just allow/block, but human escalation path |
| Policy set versioning | `mvp_policy_set v1.0` — policy versions are recorded on every audit event |
| Human-in-the-loop by architecture | Approval gate is enforced in the service layer — it cannot be removed by UI change |
| Actor-attributed audit | Every audit event records who or what took the action: USER, AI, GOVERNANCE, or SYSTEM |
| Confidence recording | AI confidence score recorded on every AI-generated event — low confidence is visible in the audit record |

---

## Likely Executive Questions and Suggested Answers

**"How is this different from just using ChatGPT with a claims prompt?"**

> "ChatGPT is a model. This is a platform. ChatGPT has no governance layer — it acts on any instruction. This platform evaluates every request against a policy engine before the model is invoked, and the evaluation is permanently recorded. ChatGPT has no audit trail. This platform records every action with actor, status, and latency. ChatGPT has no human approval gate — it would write directly to your system of record if you let it. This platform requires explicit human approval before any write operation. They are not comparable categories of software."

**"Is the AI making the decisions?"**

> "No. The AI is producing recommendations. The governance engine is enforcing policy. The adjuster is making decisions. The platform is designed so that the AI can never take a final action on its own — every AI output that could affect a system of record requires explicit human approval. Human authority is enforced by the architecture."

**"What happens when the AI is wrong?"**

> "The adjuster sees the AI output alongside the evidence it is based on. If the AI is wrong, the adjuster rejects the draft note. The rejection is recorded in the audit trail. The adjuster writes their own note. The AI output never reaches ClaimCenter without adjuster approval. The audit record shows exactly what the AI recommended and what the adjuster decided."

**"Is our claim data being sent to OpenAI?"**

> "In Phase 1, this is a demonstration running on mock data — no real claim data exists in the system. In Phase 2, we will use your enterprise model gateway, which routes to Azure OpenAI in your subscription — your data stays in your Azure tenant, subject to your data processing agreements. The `IModelProvider` interface allows us to route to any model endpoint, including fully private deployments."

**"How long will Phase 2 take?"**

> "The architecture is complete. Phase 2 is adapter implementation. The interfaces are already defined and documented. Connecting the ClaimCenter sandbox adapter, the identity provider, and the model gateway is an engineering task with a known scope. We estimate six to eight weeks for initial sandbox integration with all three adapters connected."

**"What if we change model providers in the future?"**

> "The platform routes through `IModelProvider` — a typed interface that any model provider can implement. Changing from Azure OpenAI to Anthropic, Google, or a private model is a matter of implementing the interface and updating the wiring in `dependencies.py`. The business logic, the governance controls, and the audit trail are unchanged."

**"How do we know the audit trail cannot be tampered with?"**

> "In Phase 1, the audit store is in-memory and append-only by design. In Phase 2, it will be backed by a PostgreSQL database with a write-only audit user — the application can only append, never update or delete. In Phase 3, we can move to an immutable audit ledger with cryptographic integrity proofs. The interface is already defined; only the adapter changes."

**"What does this cost to run?"**

> "Phase 1 is running on Hugging Face Docker Spaces free tier — effectively zero. In Phase 2, the primary costs are the Azure OpenAI API calls, which are billed per token and routable to the lowest-cost model that meets the quality threshold. The model router is designed to minimise cost by task type. The illustrative dashboard shows an estimated $148K monthly saving versus manual baseline at 2,481 AI-assisted claims per month."
