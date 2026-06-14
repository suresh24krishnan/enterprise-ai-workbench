# ADR-003 — Identity: On-Behalf-Of Delegation with Governed Fallback

**Status:** Accepted — OBO validation pending
**Date:** 2026-06-13
**Phase:** 2 — Enterprise Integration Foundation
**Deciders:** Platform Architecture Team, IAM, Compliance
**Supersedes:** None
**Blocks:** ADR-002 Write Milestone (no write-path contract is frozen until this decision is resolved)

---

## Context

In Phase 1, identity is mocked. The adjuster is pre-authenticated as a hardcoded user; all audit events attribute actions to this mock identity. No real identity provider is involved.

In Phase 2, two things change:

1. The platform authenticates real adjusters against a real identity provider (Okta or Azure AD).
2. When the platform calls enterprise APIs on behalf of an adjuster — ClaimCenter, the vector store, the model gateway — the API call must carry an identity token that correctly attributes the action to the adjuster, not to the platform service account.

The identity model chosen here has direct consequences for:
- **Audit attribution** — whose identity appears on ClaimCenter read and write events
- **ClaimCenter access control** — whether the adjuster's permission set is enforced on API calls
- **Write-path safety** — whether a note written to ClaimCenter is attributed to the adjuster or to a generic platform identity
- **Compliance** — whether the regulatory audit record correctly identifies the human actor responsible for every claim action

Two models are available:

**Model A — On-Behalf-Of (OBO) Delegated Identity**
The platform holds no standing access to ClaimCenter. When an adjuster is authenticated, the platform exchanges the adjuster's SSO token for a delegated token via the OAuth 2.0 On-Behalf-Of flow. ClaimCenter API calls carry the adjuster's delegated identity. Every API call is attributed to the adjuster at the ClaimCenter level — the platform's service account does not appear in ClaimCenter logs.

**Model B — Governed Service Identity with Immutable User Attribution**
The platform holds a service account with access to ClaimCenter. API calls are made by the service account. The adjuster's identity is carried as a header (`X-Acting-User-Id`, `X-Acting-User-Role`) and recorded in the platform audit trail. ClaimCenter logs show the service account, not the adjuster. The platform audit trail is the source of truth for human attribution.

---

## Decision

**Preferred model: On-Behalf-Of (OBO) Delegated Identity.**

OBO status: **pending external validation** — IAM and ClaimCenter environment access required to confirm feasibility.

**Fallback model: Governed Service Identity with Immutable User Attribution**, activated only if OBO is confirmed infeasible after external validation.

**Hard rule: No write-path contract is frozen until OBO or the approved fallback is formally decided.**

---

## OBO Model — Detail

### Flow

```
Adjuster authenticates via SSO
        │
        ▼
Platform receives adjuster access token (SSO scope)
        │
        ▼
Platform performs OBO exchange:
  POST /oauth2/token
  grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
  assertion={adjuster_access_token}
  scope=ClaimCenter.Read ClaimCenter.Write
        │
        ▼
Platform receives delegated token scoped to ClaimCenter
        │
        ▼
ClaimCenter API call carries delegated token
ClaimCenter logs: adjuster identity
Platform audit trail: adjuster identity + OBO delegation recorded
```

### Audit record under OBO

Every audit event records:
- `actor_type: USER`
- `actor_name: {adjuster.displayName}`
- `actor_id: {adjuster.employeeId}`
- `delegation_model: OBO`
- `delegated_token_scope: ClaimCenter.Read | ClaimCenter.Write`

### Prerequisites for OBO

- [ ] Azure AD or Okta configured with OBO permission grant for ClaimCenter application
- [ ] ClaimCenter sandbox registered as a resource in the identity provider
- [ ] Platform application service principal granted `ClaimCenter.Read` and `ClaimCenter.Write` scopes
- [ ] OBO flow tested against ClaimCenter sandbox with a real adjuster test account
- [ ] Token lifetime and refresh behaviour confirmed — OBO tokens typically have a 1-hour lifetime; refresh strategy required for long claims sessions

### OBO validation owner

IAM Team + ClaimCenter Integration Team
Target: confirmed or denied by end of Sprint 1

---

## Fallback Model — Detail

The fallback is activated if and only if OBO is confirmed infeasible. "Infeasible" means one or more of:
- ClaimCenter application cannot be registered as an OBO resource in the enterprise identity provider
- OBO grant permissions cannot be approved by IAM within the Phase 2 timeline
- OBO token exchange introduces latency that violates the SLA for claim load time (target: <2s claim open)

### Flow under fallback

```
Adjuster authenticates via SSO
        │
        ▼
Platform receives adjuster identity (name, ID, role, permissions)
        │
        ▼
Platform calls ClaimCenter using service account token
with headers:
  X-Acting-User-Id: {adjuster.employeeId}
  X-Acting-User-Role: {adjuster.role}
  X-Platform-Request-Id: {platform_request_id}
        │
        ▼
ClaimCenter logs: service account (platform)
Platform audit trail: adjuster identity (immutable attribution)
```

### Audit record under fallback

Every audit event records:
- `actor_type: USER`
- `actor_name: {adjuster.displayName}`
- `actor_id: {adjuster.employeeId}`
- `delegation_model: SERVICE_IDENTITY_WITH_USER_ATTRIBUTION`
- `service_account: {platform_service_account_id}`
- `platform_request_id: {uuid}`

The platform audit trail is the **authoritative** human attribution record under this model. ClaimCenter logs are not the source of truth for human identity — the platform is.

### What must be confirmed before fallback is approved

Compliance and legal must explicitly approve the following statement:

> "For the purposes of regulatory audit, the platform immutable audit trail constitutes the authoritative record of human identity for all API actions taken by the platform service account on behalf of authenticated adjusters."

This approval is required before any write-path contract is frozen under the fallback model.

---

## What Must NOT Happen

Regardless of which identity model is chosen:

1. **The service account must never be used without an authenticated adjuster session.** The platform does not make speculative or background API calls to ClaimCenter without an active adjuster session with a recorded identity.

2. **The adjuster identity must appear on every audit event** — including events generated by AI tools, governance evaluations, and system actions triggered by an adjuster workflow. There is no anonymous workflow step.

3. **Write operations must carry adjuster identity.** Under OBO: the delegated token ensures this at the ClaimCenter level. Under fallback: the `X-Acting-User-Id` header is required and validated before the write tool invocation; a write without a confirmed adjuster identity is rejected by the write framework.

4. **Identity must not be spoofed by retrieved content.** Tool outputs — including documents retrieved from ClaimCenter or the vector store — must not be able to influence the identity context for the current session. See ADR-006.

---

## Decision Gate

This ADR moves from **Accepted — OBO validation pending** to one of:

- **Accepted — OBO confirmed**: OBO prerequisites satisfied, OBO tested against sandbox
- **Accepted — Fallback approved**: OBO confirmed infeasible by IAM; compliance approval obtained for service identity model; write-path contracts may be frozen

Until this gate is resolved, write-path tool contracts (`submit_note`) remain in draft status and the write framework (ADR-002 Milestone 2) does not advance.

---

## Consequences

**Positive:**
- OBO provides the strongest possible human attribution at the ClaimCenter level — no reliance on platform audit trail for compliance
- Fallback is clearly defined with explicit compliance approval requirements — no ambiguity about what constitutes acceptable identity evidence
- Hard rule on write-path contracts prevents integration work from proceeding on an assumption that may not hold

**Negative:**
- OBO validation is an external dependency — delay in IAM response directly delays write framework timeline
- Fallback requires compliance sign-off that may take time to obtain
- Service identity fallback creates a dual-record situation (ClaimCenter logs vs. platform audit trail) that requires operational clarity

---

## Review Trigger

This ADR must be reviewed:
- When IAM provides OBO feasibility assessment (expected Sprint 1)
- If compliance rejects the service identity fallback model
- If a third identity model is proposed (e.g., certificate-bound tokens, Managed Identity)
