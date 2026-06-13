# Enterprise AI Workbench

A production-shaped enterprise AI platform demonstrating governed, explainable, human-in-the-loop AI workflows. Claims processing is the first business domain.

## What This Is

This is not an AI chatbot. It is an enterprise architecture that routes tasks to appropriate AI models, enforces governance policies, maintains an immutable audit trail, and requires human approval before any write operation.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────────────────┐
│   Frontend  │────▶│   Backend   │────▶│  Services (Router, Governance,   │
│  (React/TS) │     │  (FastAPI)  │     │  Audit, RAG, Orchestration)      │
└─────────────┘     └─────────────┘     └──────────────────────────────────┘
                                                       │
                          ┌────────────────────────────┤
                          ▼                            ▼
                   ┌─────────────┐           ┌─────────────────┐
                   │   Domains   │           │    Adapters     │
                   │  (Claims)   │           │ (ClaimCenter,   │
                   └─────────────┘           │  Identity,      │
                                             │  Models, etc.)  │
                                             └─────────────────┘
```

## Design Philosophy

**The MVP is not a throwaway prototype. It is a production-shaped prototype.**

- Architecture is built once and remains stable across phases
- Implementations are replaced, not rewritten
- All external systems are accessed through adapters (ports & adapters)
- Business logic never depends on infrastructure

## Evolution Phases

| Phase | Auth | ClaimCenter | Storage | Models |
|-------|------|-------------|---------|--------|
| 1 — Local MVP | Mock | Mock | SQLite | Mock |
| 2 — Dev/Sandbox | Enterprise SSO | Sandbox API | PostgreSQL | Enterprise gateway |
| 3 — Production | Enterprise SSO | Production API | Enterprise DB | Production gateway |

## Core Principles

- Clean / Hexagonal Architecture
- Interface-first design (depend on abstractions, never implementations)
- Governance by default — every AI interaction is governed
- Human authority over AI — no write bypasses human approval
- Immutable audit trail — every significant event is recorded

## Directory Structure

```
enterprise-ai-workbench/
├── frontend/          # React + Vite + TypeScript UI
├── backend/           # FastAPI application, routes, and DI wiring
├── services/          # Domain services (model routing, governance, audit, RAG, orchestration)
├── adapters/          # Infrastructure adapters (ports & adapters pattern)
├── domains/           # Business domain logic (Claims, future domains)
├── shared/            # Schemas, prompts, policies, shared components
├── mock-data/         # Local mock data for Phase 1 development
└── docs/              # Architecture decisions, API contracts, runbooks
```

## Quick Start

```bash
# Copy environment template
cp .env.example .env

# Start all services
docker-compose up
```

## Governed AI Workflow

```
User Request
    │
    ▼
Model Router ──▶ selects model based on task type, risk, cost
    │
    ▼
Governance Engine ──▶ ALLOW / DENY / ESCALATE
    │
    ▼ (if ALLOW or human approves ESCALATE)
AI Model ──▶ generates response
    │
    ▼
Audit Store ──▶ immutable record of every decision
    │
    ▼
Human Approval (for write operations)
    │
    ▼
Write Operation
```

## Key Interfaces

| Interface | Responsibility |
|-----------|---------------|
| `IClaimRepository` | Read/write claims |
| `IClaimNoteWriter` | Write notes back to ClaimCenter |
| `IIdentityProvider` | Authenticate and authorize users |
| `IKnowledgeProvider` | Retrieve relevant knowledge (RAG) |
| `IModelProvider` | Execute AI model calls |
| `IModelRouter` | Select the right model for a task |
| `IGovernanceEngine` | Evaluate governance policies |
| `IAuditStore` | Record audit events immutably |
| `IConversationService` | Manage conversation state |

---

## Phase 1 MVP Status

| Field | Value |
|-------|-------|
| **Status** | Complete — Frozen |
| **Version** | 1.0 MVP |
| **Architecture** | Enterprise AI Workbench |
| **Domain** | Claims (Reference Implementation) |

### Capabilities

- AI Claim Summary — governed, evidence-grounded, confidence-scored
- Governed Assistant — context-scoped conversational AI with per-turn governance
- Evidence & Explainability — ranked source citations backing every AI output
- Draft Note Generation — AI-authored adjuster notes held as DRAFT until human approval
- Human Approval — structured checklist, mandatory reviewer commitment before write-back
- Immutable Audit Trail — append-only eleven-event timeline with actor, status, and metadata
- Executive Dashboard — AI operations KPIs, model utilization, governance distribution, platform health

### Governance Controls

- Policy Evaluation — every AI action evaluated against `mvp_policy_set v1.0` (ALLOW / DENY / ESCALATE)
- Context Isolation — AI assistant scoped to authorized claim evidence; out-of-scope queries refused
- Human-in-the-loop — no AI output reaches a system of record without explicit adjuster approval
- Audit Logging — every significant event recorded with actor type, status, latency, and confidence
- Evidence Grounding — all AI outputs grounded in retrieved, cited, scored evidence sources

### Current Limitations

Mock integrations only. All external systems (ClaimCenter, identity provider, vector store, model gateway, audit ledger) are replaced by in-memory mock adapters. Production systems are intentionally deferred to Phase 2.

### Next Phase

Phase 2: Sandbox integrations — identity provider, ClaimCenter sandbox API, enterprise RAG pipeline, policy engine, immutable audit store, and live model routing. See [`docs/PHASE_1_COMPLETION_SUMMARY.md`](docs/PHASE_1_COMPLETION_SUMMARY.md) for the full Phase 2 roadmap.
