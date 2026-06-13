# services/model-router/

Model routing service — selects the right AI model for every task.

## Responsibility

The Model Router is the single decision point for AI model selection. No application code ever calls a model directly. All model calls are mediated through this service.

## Interface: `IModelRouter`

```python
class IModelRouter(Protocol):
    def select_model(self, task: ModelTask) -> ModelSelection: ...
    def get_available_models(self) -> list[ModelDescriptor]: ...
    def record_outcome(self, selection_id: str, outcome: ModelOutcome) -> None: ...
```

## Routing Dimensions

The router selects based on a combination of:

| Dimension | Description |
|-----------|-------------|
| Task type | `claim_summary`, `claim_qa`, `draft_note`, `governance_check`, `audit_explanation`, `high_risk_escalation` |
| Risk level | Low / Medium / High — high risk routes to premium model |
| Confidence | Low confidence may trigger re-routing or escalation |
| Cost | Budget-aware routing for high-volume tasks |
| Provider health | Fails over to alternate provider if primary is unhealthy |

## Supported Task Types

- `claim_summary` — summarize claim details
- `claim_qa` — answer questions about a claim
- `draft_note` — generate a ClaimCenter note draft
- `governance_check` — evaluate a request against policy
- `audit_explanation` — explain a past AI decision
- `high_risk_escalation` — premium model for escalated situations

## Phase Evolution

| Phase | Provider |
|-------|----------|
| 1 | Mock provider (deterministic responses) |
| 2+ | Anthropic / Azure OpenAI / Enterprise gateway |

Configuration is entirely via environment variables — no code changes needed between phases.
