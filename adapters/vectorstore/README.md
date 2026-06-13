# adapters/vectorstore/

Vector store adapter — knowledge retrieval for RAG.

## Responsibility

Provides the storage and retrieval layer for the RAG service. Implements embedding, indexing, and similarity search against the configured vector store backend.

## Interface Implemented

```python
class IVectorStore(Protocol):
    def search(self, query_embedding: list[float], top_k: int, filters: dict) -> list[VectorMatch]: ...
    def upsert(self, documents: list[EmbeddedDocument]) -> int: ...
    def delete(self, doc_ids: list[str]) -> int: ...
    def health_check(self) -> ProviderHealth: ...
```

## Implementations

| File | Environment Value | Description |
|------|------------------|-------------|
| `local_vector_store.py` | `KNOWLEDGE_PROVIDER=local` | In-memory search over `mock-data/knowledge/` |
| `pinecone_adapter.py` | `KNOWLEDGE_PROVIDER=pinecone` | Pinecone vector database |
| `azure_ai_search_adapter.py` | `KNOWLEDGE_PROVIDER=azure_ai_search` | Azure AI Search |

## Local (Phase 1) Behavior

The local adapter:
- Loads knowledge documents from `mock-data/knowledge/`
- Performs simple keyword/cosine similarity without a real embedding model
- Sufficient for MVP demonstration — no external API required
- Documents are chunked and indexed at startup

## Knowledge Document Types

- Claims handling procedures
- Coverage interpretation guidelines
- Regulatory requirements
- Policy language references
- Escalation criteria
