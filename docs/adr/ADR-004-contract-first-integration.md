# ADR-004 — Contract-First Integration Against Published Specifications

**Status:** Accepted
**Date:** 2026-06-13
**Phase:** 2 — Enterprise Integration Foundation
**Deciders:** Platform Architecture Team, Integration Engineering
**Supersedes:** None

---

## Context

Phase 2 introduces adapters for real enterprise systems: ClaimCenter, the identity provider, the model gateway, and the knowledge store. Each adapter must implement a typed interface defined in Phase 1 (`IClaimRepository`, `IIdentityProvider`, `IModelProvider`, `IKnowledgeProvider`).

The question is how adapter implementations should be derived. There are two approaches:

**Approach A — Imaginative mock-first:** Build adapter implementations based on what the team believes the enterprise API will look like. Write mock adapters that return data in an invented shape. Integrate later when real API access is available.

**Approach B — Contract-first from published specifications:** Derive every adapter implementation from the published API specification of the target enterprise system. Where specifications are not available, request them before building. Mock enterprise services are specification-backed — they return data in the shape the real system will return, using the field names, status codes, and error formats the real system uses.

---

## Decision

**Phase 2 adopts contract-first integration. All adapter implementations are derived from published enterprise API specifications. Mock enterprise services are specification-backed. Nothing is invented.**

### What "contract-first" means

1. **Adapter field names match the source system.** If ClaimCenter returns `claimNumber` not `claim_id`, the adapter maps `claimNumber` to the platform's `claim_id` at the adapter boundary. The mapping is explicit and documented in the adapter. The platform domain model is not changed to match the source system shape.

2. **Mock enterprise services simulate real system behaviour.** A mock ClaimCenter service returns the same HTTP status codes, error response shapes, field types, and pagination patterns as the real ClaimCenter API. An integration test that passes against the mock must pass against the real system without code changes — only environment configuration changes.

3. **Adapters are not written until the specification is available.** If the ClaimCenter API specification for a specific endpoint is not available, that adapter method is stubbed with a `NotImplementedError` and marked with a `TODO: PENDING_SPEC` annotation. Work proceeds on other adapters. The team does not invent a field name or response shape.

4. **Specification source is recorded in the adapter.** Every adapter file includes a header documenting the specification source, version, and date:

```python
# ClaimCenter Claims Read Adapter
# Specification: Guidewire ClaimCenter REST API v10.0
# Source: [internal Guidewire developer portal URL]
# Retrieved: 2026-Q3
# Endpoint: GET /cc/v1/claims/{claimId}
```

### Priority specification sources

| System | Preferred Specification Source |
|--------|-------------------------------|
| ClaimCenter | Guidewire ClaimCenter REST API documentation (Guidewire developer portal or enterprise-licensed docs) |
| Identity provider | OAuth 2.0 / OIDC specification (RFC 6749, RFC 9068) + provider-specific extension documentation (Azure AD / Okta developer docs) |
| Model gateway | Azure OpenAI REST API specification (Microsoft Learn) or Anthropic API reference |
| Knowledge store | Azure Cognitive Search REST API specification (Microsoft Learn) |
| Audit ledger | Internal enterprise audit API specification (request from Compliance / IT) |

### What to do when a specification is not available

1. **Request the specification** from the system owner before building. Document the request and the date in the adapter stub.
2. **Build the platform interface contract** (`IClaimRepository` method signatures, return types, error types) based on what the platform needs — not based on what you imagine the source system provides.
3. **Mark adapter methods as `PENDING_SPEC`** and track them in the Phase 2 risk retirement matrix.
4. **Do not invent field names or response shapes** that will need to be changed when the real specification is obtained. The cost of rework from invented shapes is higher than the cost of waiting for the specification.

---

## Rationale

### The cost of imaginative mocks

When a mock adapter is built without reference to the real system's API specification, two kinds of technical debt are created:

**Shape mismatch debt:** The mock returns `claim_id` but the real system returns `claimNumber`. When the real API is integrated, every test, every mapping, and every audit event field that used `claim_id` must be updated. The integration sprint becomes a correction sprint.

**Behaviour mismatch debt:** The mock always succeeds. The real system returns 429 when rate-limited, 404 when a claim is not found in the adjuster's portfolio, 409 when a note is submitted with a duplicate idempotency key, and 503 during maintenance windows. Tests written against an always-succeeding mock do not exercise the adapter's error handling. Error handling is written during integration — when it is hardest to test and most likely to be incomplete.

### Specification-backed mocks eliminate both debts

A specification-backed mock is derived from the same document that the real adapter implementation is derived from. The field names are the same. The error codes are the same. The pagination behaviour is the same. When the real API becomes available, the adapter implementation replaces the mock adapter behind the same interface — and the integration tests pass without modification.

### Contract-first also protects the platform domain model

The platform domain model (`Claim`, `AuditEvent`, `DraftNote`, `ApprovalRecord`) is defined by what the platform needs, not by what the source systems provide. The adapter is the translation layer. Contract-first integration makes this translation layer explicit, documented, and testable rather than implicit and ad hoc.

---

## Specification Acquisition Plan

| Adapter | Specification | Status | Action |
|---------|--------------|--------|--------|
| `ClaimCenterReadAdapter` | Guidewire ClaimCenter REST API v10.0 | Pending | Request from Guidewire account team / internal IT |
| `ClaimCenterWriteAdapter` | Guidewire ClaimCenter REST API v10.0 (write endpoints) | Pending | Same as above — write endpoints may require separate approval |
| `IdentityAdapter` (OBO) | OAuth 2.0 OBO flow (RFC 8693) + Azure AD / Okta extension | Available | RFC publicly available; provider extension from developer portal |
| `VectorSearchAdapter` | Azure Cognitive Search REST API 2023-11-01 | Available | Microsoft Learn (public) |
| `AzureOpenAIAdapter` | Azure OpenAI REST API 2024-02-01 | Available | Microsoft Learn (public) |
| `AuditLedgerAdapter` | Internal enterprise audit API | Pending | Request from Compliance / IT Architecture |

---

## Consequences

**Positive:**
- Integration tests written against specification-backed mocks pass against the real system without code changes
- Field name and behaviour mismatches are caught before real API access is obtained
- Adapter specification sources are documented — reviewers can verify implementation correctness against the original spec
- Platform domain model is protected from source system shape drift

**Negative:**
- Work on specification-pending adapters is blocked until specifications are obtained — sprint planning must account for external dependency timelines
- Guidewire specifications may require an NDA, a support portal login, or a formal request — this is an enterprise dependency, not a team decision
- Specification-backed mock services require more upfront investment than imaginative mocks

**Mitigation:**
- Specification acquisition is tracked as a risk item in the Phase 2 risk retirement matrix
- Adapter stubs with `PENDING_SPEC` annotations allow parallel work on other platform components while specifications are obtained
- Interface contracts (`IClaimRepository` method signatures) can be finalised independently of specification acquisition, since they are derived from what the platform needs

---

## Review Trigger

This ADR should be reviewed if:
- A Guidewire specification is obtained that contradicts the assumed platform interface contract
- An enterprise API uses a non-REST protocol (GraphQL, SOAP, proprietary) that requires a different adapter pattern
- A specification is so complex or versioned that a specification-lite approach for a specific low-risk endpoint is justified
