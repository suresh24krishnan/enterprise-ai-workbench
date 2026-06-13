# shared/policies/

Governance policy definitions — operator-controlled, no deployment required to update.

## Responsibility

Contains the governance policies evaluated by the Governance Engine. Policies are defined as data (YAML) rather than code — an operator can update a policy without a code change or redeployment.

## Contents (to be built)

```
shared/policies/
├── base_policy.yaml              # Default policy applicable to all task types
├── claim_summary_policy.yaml     # Rules for claim summarization
├── claim_qa_policy.yaml          # Rules for claim Q&A
├── draft_note_policy.yaml        # Rules for note drafting (strictest)
└── high_risk_policy.yaml         # Overrides for high-risk claims
```

## Policy Schema

```yaml
policy_id: draft_note_v1
task_types:
  - draft_note
rules:
  - id: require_human_approval
    condition: always
    action: ESCALATE
    reason: "All AI-drafted notes require human review before writing."

  - id: deny_pii_exposure
    condition: response_contains_pii
    action: DENY
    reason: "Response contains PII that must not be included in notes."

  - id: high_reserve_escalation
    condition: claim.reserve_amount > 100000
    action: ESCALATE
    reason: "High-reserve claims require supervisor review."
```

## Governance Decision Priority

When multiple rules match, the strictest decision wins:
`DENY` > `ESCALATE` > `ALLOW`
