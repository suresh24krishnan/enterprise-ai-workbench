# shared/schemas/

Shared data schemas — the single source of truth for cross-layer data contracts.

## Responsibility

Defines the canonical data shapes shared between the backend API, services, and domains. These schemas prevent drift between layers and ensure consistent validation throughout the system.

## Contents (to be built)

```
shared/schemas/
├── claim.py              # Claim, ClaimSummary, ClaimNote, ClaimDocument
├── user.py               # User, Role, Permission
├── conversation.py       # Conversation, ConversationTurn
├── governance.py         # GovernanceRequest, GovernanceDecision, Policy
├── audit.py              # AuditEvent, AuditQuery
├── model.py              # ModelRequest, ModelResponse, ModelDescriptor
└── knowledge.py          # KnowledgeChunk, KnowledgeQuery
```

## Usage

Backend API routes use these schemas for request/response validation.
Services use these schemas as their interface contracts.
The frontend TypeScript types are generated from these schemas.
