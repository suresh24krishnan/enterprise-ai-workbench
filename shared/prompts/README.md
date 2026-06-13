# shared/prompts/

Versioned AI prompt templates.

## Responsibility

Contains all prompt templates used by the AI services. Prompts are treated as versioned artifacts — changes are tracked, reviewed, and tested like code changes.

## Contents (to be built)

```
shared/prompts/
├── claim_summary.md          # Prompt for summarizing a claim
├── claim_qa.md               # Prompt for answering questions about a claim
├── draft_note.md             # Prompt for drafting a ClaimCenter note
├── governance_check.md       # Prompt for AI-assisted governance evaluation
└── audit_explanation.md      # Prompt for explaining a past AI decision
```

## Prompt Template Format

Prompts use a simple variable substitution format:

```
{{claim_details}}
{{coverage_summary}}
{{knowledge_context}}
{{user_question}}
```

Variables are injected at runtime by the orchestration service.

## Design Principles

- System prompts enforce role, scope, and output format constraints
- Every prompt instructs the model to cite sources from `{{knowledge_context}}`
- Prompts include explicit instructions about what the model must not do
- Prompt versions are tracked — a prompt change is an auditable event
- Prompts are never constructed by concatenating user input — injection is prevented by design
