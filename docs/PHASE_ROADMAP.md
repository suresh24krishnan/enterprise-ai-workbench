# Phase Roadmap — Enterprise AI Workbench

**Repository:** https://github.com/suresh24krishnan/enterprise-ai-workbench
**Live Demo:** https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench

---

## Roadmap Summary

| Phase | Name | Status | Tag |
|-------|------|--------|-----|
| 1 | Reference Implementation | **Complete — Live** | `v1.0.0-phase1` |
| 2 | Sandbox Integration | Planned — Q3 2026 | `v1.1.0-phase2` |
| 3 | Production Pilot | Planned — Q4 2026 | `v1.2.0` |
| 4 | Enterprise AI Workbench Platform | Planned — 2027 | `v2.0.0` |

The architecture is built once in Phase 1 and remains stable across all phases. Each phase swaps mock adapters for real integrations — no business logic is rewritten.

---

## Phase 1 — Reference Implementation

**Status:** Complete — Live
**Tag:** `v1.0.0-phase1`
**Duration:** Completed June 2026

### Objectives

1. Prove that governed, explainable, human-in-the-loop AI can be built as a stable enterprise platform — not as a one-off integration.
2. Establish the architecture that all future phases build on without modification.
3. Demonstrate the full claims AI workflow end-to-end using mock adapters for all external systems.
4. Deploy a publicly accessible reference implementation on Hugging Face Docker Spaces.

### Capabilities

| Capability | Description |
|------------|-------------|
| AI Claim Summary | Evidence-grounded, confidence-scored claim analysis with RAG citations |
| Governed Assistant | Context-scoped conversational AI with per-turn policy evaluation |
| Evidence & Explainability | Ranked source citations backing every AI output |
| Draft Note Generation | AI-authored adjuster notes held as DRAFT until human approval |
| Human Approval Gate | Structured checklist with mandatory reviewer commitment |
| Immutable Audit Trail | Eleven-event timeline with actor, status, latency, confidence |
| Executive Dashboard | AI operations KPIs, model utilization, governance distribution, platform health |

### Integrations

All integrations are mock adapters in Phase 1.

| Interface | Phase 1 Adapter | Real System (Phase 2+) |
|-----------|----------------|------------------------|
| `IClaimRepository` | `MockClaimRepository` | ClaimCenter API |
| `IIdentityProvider` | `MockIdentityProvider` | Enterprise SSO |
| `IModelProvider` | `MockModelProvider` | Azure OpenAI |
| `IKnowledgeProvider` | `MockKnowledgeProvider` | Azure Cognitive Search |
| `IAuditStore` | `InMemoryAuditStore` | PostgreSQL |
| `IGovernanceEngine` | `MockGovernanceEngine` | Rule-based policy engine |
| `IClaimNoteWriter` | `MockClaimNoteWriter` | ClaimCenter Write API |

### Deliverables

- 9-screen React SPA (TypeScript strict, Tailwind CSS, React Router v6)
- FastAPI backend with 12 API endpoints (Python 3.11, Pydantic v2)
- Hexagonal architecture with typed interfaces for all external systems
- Governance engine: ALLOW / DENY / ESCALATE per AI request
- Eleven-event immutable audit trail per claim workflow
- Multi-stage Docker build with nginx reverse proxy and supervisord
- Live deployment on Hugging Face Docker Spaces (port 7860)
- Executive, leadership, technical, and portfolio documentation suite

### Business Outcomes

- Demonstrates that AI governance is achievable without sacrificing user experience
- Provides a concrete architecture reference that stakeholders can review, test, and critique
- Establishes the interface contracts that Phase 2 adapter implementations must satisfy
- Reduces Phase 2 risk: the unknown is adapter implementation, not platform design

### Exit Criteria

- [x] All 9 screens functional end-to-end
- [x] All 12 API endpoints returning correct mock data
- [x] Governance engine evaluating every AI request
- [x] Audit trail recording all 11 events per workflow
- [x] Human approval gate enforced before write-back
- [x] Docker build producing a single deployable container
- [x] Live on Hugging Face Docker Spaces
- [x] All adapters backed by typed interfaces
- [x] Documentation suite complete

---

## Phase 2 — Sandbox Integration

**Status:** Planned
**Target:** Q3 2026
**Tag:** `v1.1.0-phase2`
**Estimated Duration:** 6–8 weeks

### Objectives

1. Connect the platform to real enterprise systems using sandbox/test environments.
2. Validate that the Phase 1 interface contracts correctly describe the behaviour of real systems.
3. Demonstrate that mock-to-real adapter swap requires zero changes to business logic.
4. Establish the security, data governance, and compliance baseline for production.

### Capabilities

All Phase 1 capabilities remain unchanged. Phase 2 adds:

| Capability | Description |
|------------|-------------|
| Real authentication | Enterprise SSO login — adjuster identity from the identity provider |
| Live claim data | Claims loaded from ClaimCenter sandbox API |
| Real write-back | Approved notes written to ClaimCenter sandbox via API |
| Enterprise RAG | Evidence retrieved from Azure Cognitive Search over real claim documents |
| Persistent audit trail | Audit events written to PostgreSQL with write-only audit user |
| Real governance evaluation | Rule-based policy engine backed by configurable policy rules |
| Live model routing | AI requests routed to Azure OpenAI (GPT-4.1-mini, GPT-4.1) |

### Integrations

| Interface | Phase 2 Adapter | Notes |
|-----------|----------------|-------|
| `IClaimRepository` | `ClaimCenterSandboxRepository` | REST adapter to ClaimCenter sandbox API |
| `IIdentityProvider` | `SSOIdentityProvider` | Okta / Azure AD integration |
| `IModelProvider` | `AzureOpenAIProvider` | Azure OpenAI in enterprise tenant |
| `IKnowledgeProvider` | `AzureCognitiveSearchProvider` | Vector search over claim document corpus |
| `IAuditStore` | `PostgreSQLAuditStore` | Append-only PostgreSQL table, write-only audit user |
| `IGovernanceEngine` | `RuleBasedGovernanceEngine` | Configurable rule engine, policy rules in database |
| `IClaimNoteWriter` | `ClaimCenterNoteWriter` | ClaimCenter sandbox write endpoint |

**Wiring change:** `backend/app/dependencies.py` — replace mock adapter instantiations with real adapters. No other file changes required.

### Deliverables

- Seven real adapter implementations (one per interface)
- PostgreSQL schema for audit store and governance rules
- Azure Cognitive Search index schema and document ingestion pipeline
- Sandbox environment configuration (`.env.sandbox`)
- Integration test suite against sandbox APIs
- Updated `docker-compose.yml` with PostgreSQL and Redis services
- Azure Container Apps deployment configuration (replaces HF Spaces for sandbox)
- Security review: secrets management, CORS restriction, TLS configuration
- Updated documentation: Phase 2 completion summary, release notes

### Business Outcomes

- Proves the platform works with real enterprise data and real AI models
- Establishes the integration patterns that production deployment will follow
- Produces real latency and accuracy metrics to replace the Phase 1 illustrative figures
- Gives compliance and legal a governance-enabled environment to review and sign off

### Exit Criteria

- [ ] SSO login working with real adjuster identities
- [ ] Claim list and claim detail loaded from ClaimCenter sandbox
- [ ] AI summary generated by Azure OpenAI over real claim documents
- [ ] Evidence retrieved from Azure Cognitive Search
- [ ] Governance engine evaluating requests against configurable rules
- [ ] Audit events persisted to PostgreSQL (confirmed across process restarts)
- [ ] Draft note written to ClaimCenter sandbox via write API
- [ ] CORS restricted to sandbox domain (no wildcard)
- [ ] All integration tests passing against sandbox APIs
- [ ] Security review completed and sign-off obtained

---

## Phase 3 — Production Pilot

**Status:** Planned
**Target:** Q4 2026
**Tag:** `v1.2.0`
**Estimated Duration:** 8–12 weeks

### Objectives

1. Run the platform with a live adjuster cohort on real production claims.
2. Validate AI quality, governance outcomes, and audit completeness at production scale.
3. Measure real business outcomes: processing time reduction, approval rate, governance violations.
4. Satisfy compliance and legal sign-off requirements for production AI in claims.

### Capabilities

All Phase 2 capabilities remain unchanged. Phase 3 adds:

| Capability | Description |
|------------|-------------|
| Production ClaimCenter | Live claim data and write-back to production ClaimCenter |
| Production model gateway | Azure OpenAI production tier with SLA and rate limits |
| Immutable audit ledger | Cryptographic integrity proofs on audit events |
| Policy engine | Enterprise-grade policy engine with audit-friendly rule versioning |
| Compliance reporting | Automated governance reports for regulatory submission |
| Role-based access control | Adjuster, supervisor, auditor, and read-only roles |
| SLA monitoring | Processing time and model latency alerts |
| Pilot cohort telemetry | Real-time KPI reporting for the pilot adjuster group |

### Integrations

| Interface | Phase 3 Adapter | Notes |
|-----------|----------------|-------|
| `IClaimRepository` | `ClaimCenterProductionRepository` | Production ClaimCenter REST API |
| `IModelProvider` | `AzureOpenAIProductionProvider` | Production tier with rate limiting and fallback |
| `IAuditStore` | `ImmutableLedgerAuditStore` | Hash-chained audit records, cryptographic integrity |
| `IGovernanceEngine` | `PolicyEngineGovernanceEngine` | Enterprise policy engine with versioned rule sets |
| `IClaimNoteWriter` | `ClaimCenterProductionNoteWriter` | Production write API with idempotency and retry |

### Deliverables

- Production adapter implementations (ClaimCenter, model gateway, audit ledger)
- Compliance report generator (PDF, Excel export)
- Role-based access control enforcement layer
- SLA monitoring and alerting configuration (Azure Monitor)
- Pilot adjuster onboarding guide
- Pilot cohort KPI dashboard (30-day, real telemetry)
- Regulatory submission package (audit trail export, governance report)
- Post-pilot assessment: accuracy, throughput, adjuster satisfaction, governance outcomes
- Production deployment runbook

### Business Outcomes

- Quantified processing time reduction vs. manual baseline
- Measured AI confidence and human approval rates on real claims
- Regulatory-grade audit trail for production claim decisions
- Adjuster satisfaction and adoption rate from the pilot cohort
- Cost per AI-assisted claim vs. manual processing baseline
- Governance violation rate and ESCALATE routing rate on real claims

### Exit Criteria

- [ ] Pilot cohort (target: 10–20 adjusters) onboarded and using the platform
- [ ] Production ClaimCenter write-back confirmed on at least 100 real claims
- [ ] Immutable audit trail with cryptographic integrity confirmed
- [ ] Compliance report generated and reviewed by legal/compliance
- [ ] Zero unrecorded AI actions during pilot period
- [ ] Processing time target met (target: ≤8 minutes end-to-end)
- [ ] Human approval rate ≥90%
- [ ] Governance allow rate ≥95%
- [ ] Adjuster satisfaction score ≥4.0/5.0
- [ ] Sign-off from compliance, legal, and IT security for production rollout

---

## Phase 4 — Enterprise AI Workbench Platform

**Status:** Planned
**Target:** 2027
**Tag:** `v2.0.0`
**Estimated Duration:** 12–18 months

### Objectives

1. Expand the platform from Claims to all AI-intensive business domains: Billing, Underwriting, Special Investigations (SIU), and Customer Service.
2. Build a shared AI operations platform: a single governance engine, policy engine, audit ledger, and model gateway serving all domains.
3. Establish the Enterprise AI Workbench as the organisation's standard platform for governed AI across all business operations.
4. Deliver compliance-grade AI reporting at the enterprise level.

### Capabilities

All Phase 3 capabilities remain in Claims. Phase 4 adds:

| Capability | Description |
|------------|-------------|
| Multi-domain support | Claims, Billing, Underwriting, SIU, Customer Service as separate domain modules |
| Shared governance platform | One policy engine governing AI across all domains |
| Enterprise audit ledger | Single immutable audit store for all AI actions across all domains |
| Enterprise model gateway | Centrally managed model routing with cost allocation by domain |
| Self-service domain onboarding | New business domains can be onboarded without modifying the platform core |
| Enterprise admin console | Policy management, audit search, user administration, cost reporting |
| Compliance dashboard | Cross-domain governance outcomes, regulatory reporting, AI usage analytics |
| Multi-tenant support | Separate policy sets and audit partitions per business unit or subsidiary |

### Domain Modules Planned

| Domain | Primary AI Use Cases | Key Integrations |
|--------|---------------------|------------------|
| **Claims** (Phase 1–3) | Summarisation, note generation, fraud signals, coverage analysis | ClaimCenter, model gateway |
| **Billing** | Payment dispute analysis, billing inquiry resolution, adjustment recommendations | Billing system, payment gateway |
| **Underwriting** | Risk assessment support, policy pricing analysis, application review | Underwriting system, external data providers |
| **SIU (Special Investigations)** | Fraud indicator analysis, pattern detection, investigation note generation | SIU case management, fraud databases |
| **Customer Service** | Intent classification, response drafting, escalation recommendations | CRM, telephony, email |

Each domain module implements the same interfaces (`IRepository`, `IWorkProduct`, `IApprovalGate`, `IAuditStore`) with domain-specific adapters. The governance engine and audit trail are shared across all domains.

### Integrations

| System | Purpose |
|--------|---------|
| Enterprise IAM | Single identity and access control for all domains and roles |
| Enterprise model gateway | Centrally managed Azure OpenAI, with quota and cost allocation per domain |
| Enterprise audit ledger | Immutable, organisation-wide AI action record with compliance reporting |
| Enterprise policy engine | Organisation-wide AI policy management with domain-specific rule sets |
| Azure Data Platform | Analytics, cost reporting, model quality monitoring |
| Enterprise SIEM | Audit event forwarding for security monitoring |

### Deliverables

- Domain module framework: extensible architecture for adding new business domains
- Billing domain module (full workflow: dispute analysis → recommendation → approval → system write)
- Underwriting domain module (risk assessment → recommendation → approval → policy system write)
- SIU domain module (fraud indicators → investigation note → supervisor approval → case system write)
- Customer Service domain module (intent classification → response draft → agent approval → CRM write)
- Enterprise admin console (React SPA: policy management, audit search, user admin, cost reporting)
- Enterprise compliance dashboard (cross-domain governance outcomes, regulatory reports)
- Platform operations runbook
- Enterprise architecture decision records (ADRs)
- Enterprise rollout and change management plan

### Business Outcomes

- Single governed AI platform replacing domain-specific point solutions
- Organisation-wide audit trail for all AI-assisted decisions
- Quantified cost savings across all AI-assisted business functions
- Regulatory-grade compliance reporting for all domains
- Reduced time-to-market for new AI use cases: new domains onboard to an existing governance framework, not a new one
- Enterprise cost transparency: model usage and cost allocated by domain, by team, by use case

### Exit Criteria

- [ ] All five domain modules live in production
- [ ] Single governance engine governing all domains
- [ ] Enterprise audit ledger recording all AI actions across all domains
- [ ] Compliance dashboard producing regulatory-grade reports for all domains
- [ ] Enterprise admin console live for policy management and audit search
- [ ] Multi-tenant isolation confirmed (separate policy sets and audit partitions per business unit)
- [ ] Cost reporting live with allocation by domain and use case
- [ ] Enterprise architecture review completed and approved
- [ ] All domain rollouts completed with adjuster/agent satisfaction ≥4.0/5.0
