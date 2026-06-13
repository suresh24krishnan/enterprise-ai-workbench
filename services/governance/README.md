# services/governance/

Governance engine — every AI action is evaluated before execution.

## Responsibility

The Governance Engine is the policy enforcement layer. It evaluates every proposed AI action against the configured policy set and returns a decision that the caller must honor.

No AI write operation may bypass governance. This is enforced architecturally, not by convention.

## Interface: `IGovernanceEngine`

```python
class IGovernanceEngine(Protocol):
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision: ...
    def get_active_policies(self) -> list[Policy]: ...
```

## Decision Outcomes

| Decision | Meaning | Action |
|----------|---------|--------|
| `ALLOW` | Request is within policy | Proceed automatically |
| `DENY` | Request violates policy | Reject immediately, explain why |
| `ESCALATE` | Request requires human review | Pause, present to human, require approval |

## Evaluation Inputs

A `GovernanceRequest` includes:

- User identity and role
- Task type and action
- Claim context (value, status, risk flags)
- Proposed AI output (for write operations)
- Confidence scores from the model

## Policy Location

Policies are defined in `shared/policies/`. The governance engine reads policies at startup and can reload on signal.

## Design Principles

- Governance is synchronous — no AI response is returned until governance completes
- Denials and escalations are recorded to the audit store
- All governance decisions are explainable — the reason is always returned
- Policies are data (YAML/JSON), not code — operators can adjust without deploying
