# ADR-001 — Supervisor + Deterministic Tools Architecture

**Status:** Accepted
**Date:** 2026-06-13
**Phase:** 2 — Enterprise Integration Foundation
**Deciders:** Platform Architecture Team
**Supersedes:** None

---

## Context

Phase 1 established a governed AI workflow using mock adapters for all external systems. Phase 2 must connect to real enterprise systems — ClaimCenter, identity providers, model gateways, vector stores, and audit infrastructure — while preserving the Phase 1 governance model and UX unchanged.

The question is: what runtime model governs how the AI supervisor interacts with enterprise tools?

Several patterns were evaluated:

1. **Autonomous multi-agent execution** — multiple independent agents collaborating without a central coordinator, each capable of invoking tools and making decisions autonomously.
2. **Supervisor + deterministic tools** — a single reasoning agent (the supervisor) that plans and synthesises, invoking strictly deterministic tools for all enterprise reads and writes.
3. **Fully deterministic pipeline** — no LLM reasoning in the workflow; deterministic rules at every step.
4. **Hybrid autonomous agents** — LLM agents with limited tool access, operating under a shared governance bus.

---

## Decision

**Phase 2 adopts the Supervisor + Deterministic Tools pattern.**

The AI supervisor performs all reasoning, planning, and synthesis. Enterprise interactions — data retrieval, evidence search, note submission, identity resolution, audit recording — are performed exclusively by deterministic tools that the supervisor invokes. Tools never reason. The supervisor never writes directly to enterprise systems.

```
┌─────────────────────────────────────────────────────────────────┐
│                       AI SUPERVISOR                             │
│                                                                 │
│  • Reasoning and planning                                       │
│  • Evidence synthesis                                           │
│  • Summary and note generation                                  │
│  • Confidence scoring                                           │
│  • Tool selection and sequencing                                │
│                                                                 │
│  Cannot: read/write enterprise systems directly                 │
│  Cannot: invoke governance, routing, or audit directly          │
└──────────┬──────────────────────────────────────────────────────┘
           │ invokes deterministic tools only
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    TOOL REGISTRY                                  │
│                                                                  │
│  read_claim(claim_id)           → ClaimCenterReadAdapter         │
│  search_evidence(query, scope)  → VectorSearchAdapter            │
│  resolve_identity(session_id)   → IdentityAdapter                │
│  submit_note(claim_id, note)    → ClaimNoteWriteAdapter *        │
│  record_audit_event(event)      → AuditStoreAdapter              │
│  evaluate_policy(context)       → GovernanceAdapter              │
│                                                                  │
│  * submit_note: disabled until write framework gate passed       │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                 ENTERPRISE SYSTEMS                                │
│  ClaimCenter · Identity Provider · Vector Store · Audit Ledger   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Why not autonomous multi-agent execution?

Autonomous multi-agent execution is appropriate for tasks where the decomposition and coordination of sub-tasks is itself the value — research synthesis across many sources, code generation pipelines, long-horizon planning. It is not appropriate as the default runtime model for a governed enterprise workflow because:

1. **Attribution is ambiguous.** When multiple agents communicate and hand off work, the audit record cannot unambiguously attribute a decision to a single actor. The Phase 1 audit model requires a clear actor type on every event.

2. **Governance is bypassed.** In a multi-agent system, an agent receiving a message from another agent has no way to verify that the original request was governance-cleared. The governance gate must be re-evaluated at every tool invocation, which multi-agent systems do not guarantee.

3. **Write controls are difficult to enforce.** If multiple agents can each invoke write tools, the human approval gate becomes a property of a specific agent's behaviour rather than an architectural invariant. An agent receiving a crafted message could invoke a write tool without human approval having been obtained.

4. **Debugging is non-linear.** When a claim workflow produces incorrect output in a multi-agent system, root cause analysis requires reconstructing the inter-agent message history. In a supervisor + tools model, the supervisor's tool call log is the complete execution record.

Autonomous multi-agent agents may be introduced in Phase 3+ as **governed tools** — the supervisor may invoke a sub-agent tool, but the sub-agent is a deterministic execution unit, not an autonomous decision-maker, and its results are returned to the supervisor for synthesis. The governance gate remains on the supervisor's tool invocation, not inside the sub-agent.

### Why deterministic tools?

A deterministic tool has three properties:

1. **Same input always produces the same output** (given stable external system state). There is no LLM reasoning inside the tool.
2. **Tool output is data, not instruction.** The tool returns a structured result. The supervisor decides what to do with it.
3. **Tool invocation is attributable.** Every tool call is logged with the invoking supervisor context, the tool name, the input parameters, and the output. This is the tool-level audit record.

These properties are what make tools safe to invoke inside a governed enterprise workflow. A tool that reasons, plans, or makes decisions is not a tool — it is an agent, and it requires its own governance context.

### Why this is the right Phase 2 model

Phase 2 is the integration foundation phase. The primary risk is not capability — the AI models can perform claims analysis at the required quality level. The primary risk is **integration correctness**: does the data retrieved match what the adjuster expects, does the written note conform to ClaimCenter's data model, does the identity context correctly delegate authority?

The supervisor + tools model isolates integration risk to the tools. Each tool can be tested independently against its enterprise adapter. The supervisor's reasoning quality can be evaluated independently using a golden dataset. The governance layer sits between the supervisor and the tools, as it did in Phase 1.

---

## Consequences

**Positive:**
- Governance gate remains on every tool invocation — inherited from Phase 1 architecture
- Attribution is unambiguous — every enterprise action is attributable to a supervisor invocation with a known request context
- Integration risk is isolated to tools — supervisor can be tested independently
- Write controls are architectural — the `submit_note` tool is disabled at the registry level until the write framework gate is passed
- Debugging is linear — tool call log is the complete execution record

**Negative:**
- Supervisor becomes a coordination bottleneck — parallel tool invocations require explicit supervisor orchestration
- Tool registry must be maintained as a first-class artifact — tool contracts, versioning, and deprecation need governance
- Future migration to governed sub-agents requires tool registry refactoring

**Neutral:**
- Future autonomous agents are not precluded — they enter as governed tools registered in the tool registry, not as peers of the supervisor

---

## Compliance with Phase 1 Architecture

This decision preserves all Phase 1 architectural invariants:

| Invariant | Phase 1 | Phase 2 |
|-----------|---------|---------|
| Governance evaluated before every AI action | `IGovernanceEngine.evaluate()` called before model invoke | `evaluate_policy` tool called before every supervisor tool invocation that affects state |
| Human approval required before write | `ApprovalGate` in service layer | `submit_note` tool gated by `ApprovalRecord` check |
| Immutable audit trail | `IAuditStore.record()` on every event | `record_audit_event` tool called by supervisor on every significant action |
| Context isolation | Conversation scoped to claim evidence | Evidence tool scope parameter enforces claim-level isolation |

---

## Review Trigger

This decision should be reviewed if:
- Parallel tool execution performance proves insufficient for SLA requirements
- A use case emerges where supervisor coordination of multiple simultaneous enterprise interactions creates unacceptable latency
- Governed sub-agent tooling is ready for evaluation in Phase 3
