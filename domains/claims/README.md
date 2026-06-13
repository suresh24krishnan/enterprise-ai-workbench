# domains/claims/

Claims domain — the first business domain of the Enterprise AI Workbench.

## Responsibility

Contains all business logic specific to insurance claims processing:

- Claim domain models (`Claim`, `ClaimSummary`, `ClaimNote`, `ClaimDocument`, `ClaimParty`)
- Business rules for claim risk classification
- Use cases (application services) for claim-related AI workflows
- Claim-specific validation and transformation logic

## Structure (to be built)

```
domains/claims/
├── models.py              # Claim, ClaimNote, ClaimDocument, ClaimParty, Coverage
├── use_cases/
│   ├── summarize_claim.py        # Generate AI summary of a claim
│   ├── answer_claim_question.py  # Answer a question about a claim
│   └── draft_claim_note.py       # Draft a ClaimCenter note with AI
├── policies/
│   └── claim_risk_classifier.py  # Classify claim risk level
└── schemas/
    └── claim_schemas.py          # Pydantic request/response schemas
```

## Core Domain Models

```python
class Claim:
    claim_id: str
    claim_number: str
    status: ClaimStatus
    type: ClaimType
    date_of_loss: date
    reserve_amount: Decimal
    risk_level: RiskLevel        # LOW | MEDIUM | HIGH
    parties: list[ClaimParty]
    coverages: list[Coverage]
    notes: list[ClaimNote]
    documents: list[ClaimDocument]

class ClaimNote:
    note_id: str
    claim_id: str
    content: str
    author: str
    authored_at: datetime
    is_ai_generated: bool
    approved_by: str | None
    governance_decision: str | None
```

## Risk Classification

Claims are classified by risk level based on:
- Reserve amount thresholds
- Claim type (liability, property, medical, etc.)
- Litigation flags
- Coverage complexity
- Prior claim history

Risk level feeds into the Model Router (high-risk → premium model) and Governance Engine (high-risk → ESCALATE threshold).

## AI Use Cases

| Use Case | Task Type | Governance Threshold |
|----------|-----------|---------------------|
| Summarize claim | `claim_summary` | ALLOW for all risk levels |
| Answer question | `claim_qa` | ALLOW for low/medium; ESCALATE for high-risk sensitive questions |
| Draft note | `draft_note` | Always requires human approval before write |
