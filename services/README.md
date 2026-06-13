# services/

Internal domain services that implement the core AI workbench capabilities.

## Responsibility

Each service is a focused module with a clear interface contract. Services depend on adapters (via interfaces) and on each other — never on infrastructure directly.

## Services

| Service | Interface | Responsibility |
|---------|-----------|----------------|
| `model-router/` | `IModelRouter` | Select the right AI model for a given task |
| `governance/` | `IGovernanceEngine` | Evaluate every AI action against policy |
| `audit/` | `IAuditStore` | Record every significant event immutably |
| `rag/` | `IKnowledgeProvider` | Retrieve relevant knowledge for AI context |
| `orchestration/` | `IConversationService` | Coordinate multi-step AI workflows |

## Design Constraints

- Services are pure Python — no HTTP, no framework-specific code
- Services depend on interfaces only — never on adapter implementations
- Services are injected into the backend via dependency injection
- A service may call other services but always through their interfaces
- No service writes directly to any external system — that is the adapter's job

## Governed AI Flow

Every AI-generating action follows this sequence:

```
IModelRouter.select_model(task)
    │
    ▼
IGovernanceEngine.evaluate(task, context)
    │
    ├── DENY  ──▶ return denial to user
    ├── ESCALATE ──▶ require human approval
    └── ALLOW
         │
         ▼
    IModelProvider.generate(prompt, model)
         │
         ▼
    IAuditStore.record(event)
```
