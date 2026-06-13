# adapters/

Infrastructure adapters — the boundary between business logic and the outside world.

## Responsibility

Adapters implement the interfaces defined by the domain and services. They are the only code that touches external systems (APIs, databases, AI providers, identity systems). All adapters are replaceable without changing any business logic.

This is the "ports and adapters" (hexagonal architecture) pattern.

## Adapters

| Adapter | Interface | External System |
|---------|-----------|----------------|
| `claimcenter/` | `IClaimRepository`, `IClaimNoteWriter` | Guidewire ClaimCenter |
| `identity/` | `IIdentityProvider` | Azure AD / Okta / Mock |
| `models/` | `IModelProvider` | Anthropic / Azure OpenAI / Mock |
| `vectorstore/` | `IKnowledgeProvider` (storage layer) | Pinecone / Azure AI Search / Local |
| `auditstore/` | `IAuditStore` | Splunk / Elastic / SQLite |

## Selection at Runtime

The backend selects the correct adapter implementation at startup based on environment variables:

```
IDENTITY_PROVIDER=mock        → adapters/identity/mock_identity_provider.py
CLAIMCENTER_ADAPTER=mock      → adapters/claimcenter/mock_claim_repository.py
MODEL_PROVIDER=mock           → adapters/models/mock_model_provider.py
AUDIT_STORE=sqlite            → adapters/auditstore/sqlite_audit_store.py
KNOWLEDGE_PROVIDER=local      → adapters/vectorstore/local_knowledge_provider.py
```

In Phase 2+, change the environment variable — no code changes required.

## Design Constraints

- Adapters implement interfaces only — they contain zero business logic
- Adapters may have their own dependencies (HTTP clients, DB connections) but these are encapsulated
- Mock adapters return deterministic, realistic data from `mock-data/`
- Every adapter can be health-checked independently
- Adapters handle their own error translation — they raise domain exceptions, not infrastructure exceptions
