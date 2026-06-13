# adapters/models/

Model adapter — executes AI model calls for all task types.

## Responsibility

Implements `IModelProvider` against the configured AI provider. The model router selects which model to use; this adapter executes the call and returns a structured result.

## Interface Implemented

```python
class IModelProvider(Protocol):
    def generate(self, request: ModelRequest) -> ModelResponse: ...
    def get_available_models(self) -> list[ModelDescriptor]: ...
    def health_check(self) -> ProviderHealth: ...
```

## Implementations

| File | Environment Value | Description |
|------|------------------|-------------|
| `mock_model_provider.py` | `MODEL_PROVIDER=mock` | Returns scripted, deterministic responses |
| `anthropic_adapter.py` | `MODEL_PROVIDER=anthropic` | Calls Anthropic Claude API |
| `azure_openai_adapter.py` | `MODEL_PROVIDER=azure_openai` | Calls Azure OpenAI |
| `enterprise_gateway_adapter.py` | `MODEL_PROVIDER=enterprise_gateway` | Enterprise model gateway |

## ModelRequest Schema

```python
class ModelRequest:
    model_id: str
    task_type: TaskType
    system_prompt: str
    user_prompt: str
    context_chunks: list[KnowledgeChunk]
    max_tokens: int
    temperature: float
    metadata: dict                   # passed through for audit
```

## ModelResponse Schema

```python
class ModelResponse:
    response_id: str
    model_id: str
    content: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    finish_reason: str
    metadata: dict
```

## Mock Behavior

The mock provider:
- Returns realistic but scripted responses per task type
- Simulates latency (configurable delay)
- Returns plausible token counts
- Never calls any external API — safe for offline development
