---
title: Enterprise AI Workbench
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# Enterprise AI Workbench

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Hugging%20Face%20Spaces-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench)
[![GitHub](https://img.shields.io/badge/GitHub-enterprise--ai--workbench-181717?logo=github)](https://github.com/suresh24krishnan/enterprise-ai-workbench)
[![Phase](https://img.shields.io/badge/Phase-1.1%20Deployed-22c55e)](https://github.com/suresh24krishnan/enterprise-ai-workbench)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal-6366f1)](docs/PHASE_1_COMPLETION_SUMMARY.md)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

**A production-shaped enterprise AI platform for governed, explainable, human-in-the-loop AI workflows.**

> **Live Demo →** [huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench](https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench)
> **Source →** [github.com/suresh24krishnan/enterprise-ai-workbench](https://github.com/suresh24krishnan/enterprise-ai-workbench)

---

## The Business Problem

Enterprise AI adoption in regulated industries stalls not because the models are inadequate, but because organizations cannot answer three questions from compliance, legal, and operations:

1. **Who authorised this AI action?** — No actor-level attribution on AI decisions.
2. **Why did the AI produce this output?** — No evidence trail, no confidence scoring, no explainability.
3. **What stopped the AI from acting on bad data?** — No governance layer between model output and system writes.

Without answers to these questions, AI stays in pilot. The Enterprise AI Workbench exists to answer all three — in production architecture, not in prototype code.

---

## Solution Overview

The Workbench is a **reference implementation of governed AI for claims processing** — the first business domain in what is designed to be a multi-domain enterprise AI platform.

It demonstrates that enterprise AI can be:

- **Governed by default** — every AI action evaluated against a policy engine before execution
- **Fully explainable** — every output grounded in cited, scored evidence sources
- **Human-in-the-loop** — no AI output reaches a system of record without explicit human approval
- **Immutably audited** — every significant event recorded with actor type, status, latency, and confidence
- **Architecture-stable** — Phase 1 mock adapters are swapped for real integrations in Phase 2 with zero business logic changes

---

## Live Demo

**[→ Launch the Enterprise AI Workbench](https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench)**

Walk the full claims AI workflow:

| Screen | What It Shows |
|--------|--------------|
| Executive Dashboard | AI operations KPIs, model utilization, governance distribution, platform health |
| Claims Workbench | Claim list → claim detail → governed AI actions |
| AI Claim Summary | Evidence-grounded, confidence-scored summary with RAG citations |
| Governed Assistant | Context-scoped conversational AI with per-turn policy evaluation |
| Evidence & Explainability | Ranked evidence sources backing every AI output |
| Draft Note Generation | AI-authored adjuster note held as DRAFT until human approval |
| Human Approval | Structured checklist with mandatory reviewer commitment |
| Audit Trail | Eleven-event immutable timeline with actor, status, latency, confidence |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Browser (React + TypeScript)                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTPS
┌───────────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11)                      │
│                                                                      │
│  Routes ──▶ Services ──▶ Governance Engine ──▶ Model Router          │
│                │                                     │               │
│                ▼                                     ▼               │
│         Audit Store                           AI Model Provider      │
│                │                                     │               │
│                └──────────────────┬──────────────────┘               │
│                                   ▼                                  │
│                        Ports & Adapters Layer                        │
│             (IClaimRepository, IIdentityProvider, ...)               │
└──────────────────────────────────────────────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
   ClaimCenter API          Identity Provider         Model Gateway
   (Phase 2: Sandbox)       (Phase 2: SSO)        (Phase 2: Enterprise)
   (Phase 1: Mock)          (Phase 1: Mock)        (Phase 1: Mock)
```

**Design rule:** Business logic never depends on infrastructure. Every external system is accessed through a typed interface. Swapping `MockClaimRepository` for `ClaimCenterRepository` in `dependencies.py` is the only change required to move from Phase 1 to Phase 2.

---

## End-to-End Governed Workflow

```
Adjuster opens claim
        │
        ▼
Identity Provider ──▶ authenticates user, establishes session
        │
        ▼
Claim Repository ──▶ loads claim data, evidence, history
        │
        ▼
Model Router ──▶ selects model (task type, risk level, cost)
        │
        ▼
Governance Engine ──▶ evaluates policy set
        │
        ├──▶ ALLOW  ──▶ AI executes, result returned
        ├──▶ DENY   ──▶ action blocked, reason recorded
        └──▶ ESCALATE ──▶ routed to human reviewer
                │
                ▼
        AI generates output (summary / note / analysis)
                │
                ▼
        Evidence retrieved and ranked (RAG)
                │
                ▼
        Audit Store ──▶ event recorded (immutable, append-only)
                │
                ▼
        Human Approval ──▶ adjuster reviews, commits, or rejects
                │
                ▼
        Write-back (Phase 2: ClaimCenter API)
                │
                ▼
        Audit Store ──▶ write-back event recorded
```

---

## Governance Controls

| Control | Mechanism | Phase 1 |
|---------|-----------|---------|
| Policy evaluation | ALLOW / DENY / ESCALATE per request | Mock policy engine — `mvp_policy_set v1.0` |
| Context isolation | AI scoped to authorized claim evidence only | Enforced in conversation service |
| Human authority | No write reaches a system of record without human approval | Approval gate before all write operations |
| Audit logging | Append-only event log with actor type, status, latency, confidence | In-memory audit store |
| Evidence grounding | Every AI output grounded in cited, ranked sources | Mock RAG with realistic evidence |
| Model routing | Task-appropriate model selected before execution | Mock router (GPT-4.1-mini / Claude Sonnet / Gemini Flash) |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript (strict), Vite 5, Tailwind CSS v3, React Router v6 |
| Backend | Python 3.11, FastAPI, Pydantic v2, pydantic-settings |
| Architecture | Hexagonal (Ports & Adapters), Repository Pattern, Dependency Injection |
| Container | Docker multi-stage, nginx reverse proxy, supervisord, Python 3.11-slim |
| Deployment | Hugging Face Docker Spaces, port 7860 |
| Phase 2 target | Azure OpenAI, Azure Cognitive Search, PostgreSQL, enterprise SSO |

---

## Phase Roadmap

| Version | Name | Key Changes |
|---------|------|-------------|
| `v1.0.0-phase1` | Reference Implementation | Full governed workflow, mock adapters, immutable audit trail |
| `v1.1.0-phase2` | Sandbox Integration | Real identity provider, ClaimCenter sandbox API, PostgreSQL, enterprise RAG |
| `v1.2.0` | AI Layer | Azure OpenAI integration, real model routing, policy engine, immutable audit ledger |
| `v2.0.0` | Enterprise Platform | Multi-domain support, production ClaimCenter, compliance reporting, SLA monitoring |

See [`docs/RELEASE_STRATEGY.md`](docs/RELEASE_STRATEGY.md) for the full release approach.

---

## Quick Start

### Run locally with Docker

```bash
# Clone
git clone https://github.com/suresh24krishnan/enterprise-ai-workbench.git
cd enterprise-ai-workbench

# Build and run
docker-compose up --build

# Open
open http://localhost:7860
```

### Run backend + frontend separately (development)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## Directory Structure

```
enterprise-ai-workbench/
├── frontend/          # React + Vite + TypeScript SPA
│   ├── src/
│   │   ├── pages/     # ExecutiveDashboard, ClaimsWorkbench, AuditTimeline, ...
│   │   ├── components/# Layout, shared UI components
│   │   ├── lib/       # api.ts — single API client
│   │   └── types/     # TypeScript interfaces (snake_case, matches backend)
│   └── nginx.conf     # nginx reverse proxy config (Docker deployment)
├── backend/           # FastAPI application, routes, DI wiring
│   └── app/
│       ├── api/       # Route handlers (claims, conversation, session, health)
│       ├── config.py  # pydantic-settings configuration
│       └── repositories/ # MockClaimRepository (Phase 1)
├── services/          # Domain services (model router, governance, audit, RAG, orchestration)
├── adapters/          # Infrastructure adapters (ports & adapters interfaces)
├── domains/           # Business domain logic (Claims)
├── shared/            # Schemas, prompts, policies
├── mock-data/         # Phase 1 mock data
├── docs/              # Architecture, release strategy, versioning, leadership docs
├── Dockerfile         # Multi-stage production build
├── docker-compose.yml # Single-container deployment
├── supervisord.conf   # Process manager (nginx + uvicorn)
└── start.sh           # Container entrypoint
```

---

## Key Interfaces

| Interface | Responsibility |
|-----------|---------------|
| `IClaimRepository` | Read/write claims — swap mock for ClaimCenter in Phase 2 |
| `IClaimNoteWriter` | Write notes to ClaimCenter — mock in Phase 1 |
| `IIdentityProvider` | Authenticate and authorize users — mock in Phase 1 |
| `IKnowledgeProvider` | Retrieve evidence (RAG) — mock in Phase 1 |
| `IModelProvider` | Execute AI model calls — mock in Phase 1 |
| `IModelRouter` | Select the right model for a task |
| `IGovernanceEngine` | Evaluate policy before every AI action |
| `IAuditStore` | Record audit events immutably |

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/PHASE_1_COMPLETION_SUMMARY.md`](docs/PHASE_1_COMPLETION_SUMMARY.md) | Full Phase 1 capability summary, architecture decisions, demo script |
| [`docs/RELEASE_STRATEGY.md`](docs/RELEASE_STRATEGY.md) | One-repo strategy, version path, HF Space deployment model |
| [`docs/VERSIONING_GUIDE.md`](docs/VERSIONING_GUIDE.md) | Tag naming, release naming, recommended commands |
| [`docs/LEADERSHIP_ONE_PAGER.md`](docs/LEADERSHIP_ONE_PAGER.md) | Executive summary for leadership review |
| [`docs/RELEASE_NOTES_v1.0.md`](docs/RELEASE_NOTES_v1.0.md) | Phase 1 release notes |
| [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md) | Phase 1 scope boundaries |
