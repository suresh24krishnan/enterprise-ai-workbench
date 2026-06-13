# services/rag/

Retrieval-Augmented Generation (RAG) service — grounds AI responses in enterprise knowledge.

## Responsibility

Retrieves relevant documents, policies, and knowledge to include in AI prompts. Ensures AI responses are grounded in authoritative enterprise content rather than model hallucination.

## Interface: `IKnowledgeProvider`

```python
class IKnowledgeProvider(Protocol):
    def retrieve(self, query: KnowledgeQuery) -> list[KnowledgeChunk]: ...
    def index_document(self, document: Document) -> str: ...  # returns doc_id
    def health_check(self) -> ProviderHealth: ...
```

## Knowledge Sources (by phase)

| Phase | Source |
|-------|--------|
| 1 | Local markdown/JSON files in `mock-data/` |
| 2+ | Enterprise vector database (Pinecone, Azure AI Search, etc.) |

## Retrieval Flow

```
User question
    │
    ▼
Embed query ──▶ Vector search ──▶ Top-K chunks
    │
    ▼
Rank and filter by relevance threshold
    │
    ▼
Return chunks with source metadata
    │
    ▼
Included in AI prompt as grounded context
```

## Knowledge Chunk Schema

```python
class KnowledgeChunk:
    chunk_id: str
    source_document: str
    source_url: str | None
    content: str
    relevance_score: float
    metadata: dict
```

## Design Constraints

- Every retrieval is audited
- Source citations are always returned with chunks
- Chunks are included verbatim — AI is instructed to cite sources
- Retrieval failures do not silently drop context — they surface as warnings
