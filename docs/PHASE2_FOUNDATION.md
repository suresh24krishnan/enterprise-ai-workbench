# Phase 2 Integration Foundation

**Sprint:** 0.5 — Enterprise Integration Foundation Skeleton
**Branch:** `phase-2-enterprise-integration-foundation`
**Package:** `backend/app/integration/`

---

## Why this package exists

Phase 1 connected every service directly to mock implementations — the repository, AI provider, and audit store were all wired at import time with no abstraction for swapping them out. This worked for Phase 1 because the goal was to demonstrate the workflow, not to integrate with enterprise systems.

Phase 2 must connect to real enterprise systems: ClaimCenter, the identity provider, the AI model gateway, and the enterprise knowledge store. Connecting directly — importing real adapters where mock imports currently live — would mean that switching between development (mock), testing (specification-backed mock), and production (real) requires code changes. Code changes introduce risk and reduce the team's ability to test in isolation.

The integration package solves this by placing a registry between the application and its providers. The application asks the registry for a provider by name. The registry returns the right implementation based on configuration. No application code changes when a provider switches from mock to real.

---

## Why MOCK is the permanent default

The default for every provider in every environment is `MOCK`.

This is not a temporary scaffolding decision. It is a deliberate safety policy:

- **Development safety:** A developer who pulls the branch and runs the application without any `.env` configuration gets mock providers. No risk of accidentally hitting enterprise systems with test data.
- **CI safety:** The CI pipeline runs against mock providers without requiring enterprise credentials in the CI environment.
- **Onboarding safety:** A new team member can run the full application locally from day one without requesting enterprise access.
- **Incident containment:** If an environment variable is misconfigured and a provider's mode cannot be determined, the registry falls back to the configured value — and the configured default is MOCK, not REAL.

Switching any provider to REAL requires an explicit environment variable (`PROVIDER_CLAIMCENTER=real`). Silence is safe. Noise is safe. Only explicit configuration can activate real enterprise connectivity.

---

## Why REAL fails fast instead of falling back silently

If a provider is configured for `REAL` mode but no real adapter factory is registered, the registry raises `IntegrationConfigError` immediately at the first resolution attempt. The application does not start in a degraded state.

Silent fallback — quietly returning a mock provider when REAL was requested — is more dangerous than a startup failure because:

1. **The failure is invisible.** The application starts and appears healthy. The adjuster uses the platform and sees mock data. No error is logged. No alert fires. The misconfiguration may go undetected for hours or days.

2. **The audit trail is wrong.** If the platform believes it is in REAL mode but is actually using mock providers, audit events record actions against a real claim but the underlying data is fabricated. This is a compliance integrity issue.

3. **Debugging is hard.** When the misconfiguration is eventually discovered, determining the scope of affected claims and audit events requires forensic analysis rather than a simple startup log.

A startup failure with a clear error message is always preferable. The error tells the operator exactly what is wrong: which provider is misconfigured, what configuration is needed, and how to fix it. No forensic analysis required.

---

## Why silent fallback is specifically dangerous in claims processing

In a regulated claims environment, the data source for every AI output must be known and attributable. If the platform silently uses mock evidence to generate a claim summary that an adjuster then approves and submits to ClaimCenter, the adjuster has approved a note based on fabricated evidence. This is not recoverable by fixing the configuration — it requires a compliance investigation to determine which claims were affected and what notes must be voided.

The fail-fast policy prevents this class of incident at the cost of a startup failure, which is always recoverable.

---

## Why read and write contracts will be separated

Phase 2 separates read integrations from write integrations as separate milestones with independent exit criteria (ADR-002). The contract structure in `integration/contracts/` will reflect this separation:

- Read contracts define what the application may retrieve from enterprise systems: claim records, evidence documents, policy terms, claim history.
- Write contracts define what the application may submit: adjuster notes, audit events, claim status updates.

Write contracts have additional safety requirements not present in read contracts:
- Human approval record must be verified before any write is invoked
- Idempotency key must be present on every write request
- Read-back after write must be implemented to verify the write succeeded
- Write tools are disabled at the registry level until all write-gate conditions are satisfied (ADR-002)

Separating the contracts makes these constraints explicit at the type level rather than embedded in business logic.

---

## Why provider abstraction exists instead of direct imports

Direct imports — `from backend.app.mocks.claim_repository import MockClaimRepository` — couple the application to a specific implementation at import time. Changing providers requires changing import statements, which means changing application code.

Provider abstraction — `registry.resolve("claimcenter")` — decouples the application from the implementation. The application's service layer asks for a `claimcenter` provider and receives whatever implementation the registry has been configured to return. Changing from mock to real requires only a configuration change and a registered real factory. No application service code changes.

This is the hexagonal architecture principle (ports and adapters) applied to enterprise integrations: the application core depends on an abstract interface (the contract), not on a concrete implementation (the adapter).

---

## Why no enterprise APIs are connected yet

Phase 2 Sprint 0.5 establishes the integration infrastructure — the package structure, the mode system, the registry, and the configuration — without connecting any enterprise APIs.

Enterprise connectivity requires:
1. API specifications from Guidewire, Azure, and the enterprise IT team (ADR-004 — being acquired in Sprint 1)
2. Identity model resolution — OBO or governed fallback (ADR-003 — pending IAM validation in Sprint 1)
3. Network access and credentials for lower-environment enterprise systems (being provisioned)
4. Specification-backed mock providers that simulate real system behaviour (Sprint 2)

Building the integration package now — before any of these are available — ensures that when specifications arrive, the Sprint 1 and Sprint 2 work can proceed immediately without needing to design the package structure at the same time as implementing adapter logic.

---

## Why Guidewire specifications will drive Sprint 1 contracts

The contract-first policy (ADR-004) requires that all adapter interface definitions be derived from the published API specification of the target system, not invented from assumptions about what the system provides.

The ClaimCenter contract (`contracts/claimcenter.py`, Sprint 1) will define exactly the field names, return types, error types, and pagination behaviour that the Guidewire ClaimCenter REST API specification documents. The mock provider (Sprint 2) will implement the same contract using the same field names and simulating the same error codes. When the real ClaimCenter adapter (Sprint 2+) replaces the mock behind the same contract, integration tests pass without modification.

Contracts are not written until specifications are received. Adapter methods that depend on unavailable specifications are stubbed with `raise NotImplementedError("PENDING_SPEC: ...")` and tracked in the risk retirement matrix (R2 — ClaimCenter Specification Unavailable).

---

## How this foundation enables future adapter substitution

The registry pattern means that swapping a provider from mock to real is a three-step process with no application code changes:

1. **Implement the real adapter** that satisfies the same contract as the mock: same method signatures, same return types, same error types.
2. **Register the real factory** in `dependencies.py` (the single wiring point): `registry.register_real("claimcenter", lambda: ClaimCenterAdapter(config))`.
3. **Set the environment variable**: `PROVIDER_CLAIMCENTER=real`.

Step 3 alone is what the operator changes in a deployment. Steps 1 and 2 happen once during Sprint 2 adapter development. From that point forward, switching ClaimCenter between mock and real is a configuration change, not a code change.

This is what makes the integration milestones in the execution plan (ADR-002, PHASE2_EXECUTION_PLAN.md) safe: each provider migrates independently, the application works at every intermediate state, and no application code changes are required to activate or deactivate real enterprise connectivity.

---

## Package structure reference

```
backend/app/integration/
├── __init__.py          Entry point documentation
├── config.py            IntegrationConfig — provider mode settings, env var mapping
├── modes.py             ProviderMode enum — MOCK | HYBRID | REAL
├── registry.py          ProviderRegistry — register, resolve, fail fast on REAL
├── contracts/
│   └── __init__.py      Provider interface contracts (Sprint 1)
├── mocks/
│   └── __init__.py      Specification-backed mock providers (Sprint 2)
└── providers/
    └── __init__.py      Real enterprise adapter implementations (Sprint 2+)
```

---

## Configuration reference

| Variable | Default | Effect |
|----------|---------|--------|
| `INTEGRATION_MODE` | `mock` | Global default for all providers |
| `PROVIDER_CLAIMCENTER` | `mock` | ClaimCenter provider mode |
| `PROVIDER_POLICYCENTER` | `mock` | PolicyCenter provider mode |
| `PROVIDER_EDW` | `mock` | Enterprise Data Warehouse mode |
| `PROVIDER_DOCUMENTS` | `mock` | Document store mode |
| `PROVIDER_FRAUD` | `mock` | Fraud detection mode |
| `PROVIDER_EMAIL` | `mock` | Email/notification mode |

Setting any provider to `real` with no registered real adapter raises `IntegrationConfigError` at startup. This is intentional.
