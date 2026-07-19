# CodeCoroner — Vector Search Design

## Architecture

```
Code Chunks
    │
    ▼
┌────────────────────┐     ┌────────────────────┐
│   Embedding Gen     │     │   Full-Text Search  │
│   (nomic-embed-text)│     │   (PostgreSQL FTS)  │
│   → 768-dim vector  │     │   → tsvector index  │
└─────────┬──────────┘     └──────────┬───────────┘
          │                           │
          ▼                           ▼
┌────────────────────┐     ┌────────────────────┐
│   pgvector Store    │     │   tsquery Search   │
│   Cosine Similarity │     │   BM25-like rank   │
│   IVFFlat Index     │     │   GIN Index        │
└─────────┬──────────┘     └──────────┬───────────┘
          │                           │
          └──────────┬───────────────┘
                     ▼
          ┌────────────────────┐
          │   Fusion & Rerank   │
          │   Weighted sum 0.7  │
          │   + Re-rank with    │
          │   cross-encoder     │
          └────────────────────┘
```

## Chunking Strategy

### Semantic Chunking (AST-based via Tree-sitter)

| Chunk Type | Strategy | Max Size |
|---|---|---|
| `function` | Entire function body | 200 lines |
| `class` | Entire class (without methods) | 100 lines |
| `method` | Single method within class | 100 lines |
| `block` | Top-level code block | 100 lines |
| `module` | Module-level imports + docstring | 50 lines |
| `docstring` | Module/class/function docstring | 50 lines |

### Chunking Algorithm

```python
class SemanticChunker:
    def chunk_file(self, file_path: str, language: str) -> list[CodeChunk]:
        """
        1. Parse file with Tree-sitter
        2. Walk AST depth-first
        3. For each node:
           - If node is a function/method definition → function chunk
           - If node is a class definition → class chunk
           - If within a class method → method chunk (linked to class)
           - If module-level docstring → docstring chunk
           - If import statements → module chunk
           - Remaining: block chunks of max 100 lines
        4. Assign each chunk a parent_chunk_id for class→method hierarchy
        5. Return ordered list of chunks
        """
```

### Chunk Overlap Strategy

- No overlap between adjacent chunks of same type
- Functions/methods are atomic — never split mid-function
- Classes include signature + docstring, methods are separate children
- Block chunks have 10-line overlap for continuity

### Filtered Languages (MVP)

| Language | Extensions | Tree-sitter Grammar |
|---|---|---|
| Python | `.py` | `tree-sitter-python` |
| TypeScript | `.ts`, `.tsx` | `tree-sitter-typescript` |
| JavaScript | `.js`, `.jsx`, `.mjs` | `tree-sitter-javascript` |
| Go | `.go` | `tree-sitter-go` |
| Rust | `.rs` | `tree-sitter-rust` |
| Java | `.java` | `tree-sitter-java` |
| C++ | `.cpp`, `.hpp`, `.cc`, `.h` | `tree-sitter-cpp` |

## Embedding Model

- **Model**: `nomic-embed-text` (Ollama)
- **Dimensions**: 768
- **Normalization**: L2-normalized for cosine similarity
- **Batching**: 32 chunks per request
- **Caching**: Skip if chunk hash unchanged

### Prefix Strategy

```python
PREFIX_MAP = {
    'function':  'function: ',
    'class':     'class: ',
    'method':    'method: ',
    'block':     'code: ',
    'module':    'module: ',
    'docstring': 'docstring: ',
}

def embed_input(text: str, chunk_type: str) -> str:
    """Pre-pend type prefix for better semantic separation."""
    prefix = PREFIX_MAP.get(chunk_type, 'code: ')
    return prefix + text
```

## Vector Index

### IVFFlat Index (MVP)

```sql
CREATE INDEX idx_chunk_embeddings_ivfflat
    ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

- **Lists**: `sqrt(n)` where n = estimated rows (~10k chunks → 100 lists)
- **Probes**: `SET ivfflat.probes = 10;` per query for recall/speed tradeoff

### HNSW Index (Post-MVP, pgvector ≥ 0.5)

```sql
CREATE INDEX idx_chunk_embeddings_hnsw
    ON chunk_embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);
```

## Hybrid Search Strategy

```python
class HybridSearchEngine:
    def __init__(self, db: Database, semantic_weight: float = 0.7):
        self.db = db
        self.semantic_weight = semantic_weight
        self.keyword_weight = 1.0 - semantic_weight

    async def search(self, query: str, repo_id: str,
                     top_k: int = 20) -> list[SearchResult]:
        # 1. Generate query embedding
        query_embedding = await self.embed(query)

        # 2. Build FTS query
        tsquery = self._build_tsquery(query)

        # 3. Execute hybrid SQL
        results = await self.db.fetch_all("""
            WITH semantic AS (
                SELECT c.id, c.content, c.file_id, 1 - (ce.embedding <=> :q_emb) AS score
                FROM code_chunks c
                JOIN chunk_embeddings ce ON ce.chunk_id = c.id
                JOIN indexed_files f ON f.id = c.file_id
                WHERE f.repository_id = :repo_id
                  AND 1 - (ce.embedding <=> :q_emb) > 0.5
                ORDER BY score DESC
                LIMIT :sem_k
            ),
            keyword AS (
                SELECT c.id, c.content, c.file_id,
                       ts_rank(to_tsvector('english', c.content), :q_tsq) AS score
                FROM code_chunks c
                JOIN indexed_files f ON f.id = c.file_id
                WHERE f.repository_id = :repo_id
                  AND to_tsvector('english', c.content) @@ :q_tsq
                ORDER BY score DESC
                LIMIT :kw_k
            ),
            combined AS (
                SELECT id, content, file_id, score, 'semantic' AS match_type
                FROM semantic
                UNION ALL
                SELECT id, content, file_id, score, 'keyword'
                FROM keyword WHERE id NOT IN (SELECT id FROM semantic)
            )
            SELECT id, content, file_id, score, match_type,
                   ROW_NUMBER() OVER (ORDER BY score DESC) AS rank
            FROM combined
            ORDER BY (:sem_w * CASE WHEN match_type='semantic' THEN score ELSE 0 END
                    + :kw_w * CASE WHEN match_type='keyword' THEN score ELSE 0 END) DESC
            LIMIT :top_k
        """, values={
            'q_emb': query_embedding,
            'q_tsq': tsquery,
            'repo_id': repo_id,
            'sem_k': top_k * 2,
            'kw_k': top_k * 2,
            'sem_w': self.semantic_weight,
            'kw_w': self.keyword_weight,
            'top_k': top_k,
        })

        return [SearchResult(**r) for r in results]
```

## Reranking Strategy

### MVP: No reranker (score-based ranking only)

### V1: Cross-encoder reranker

```python
class CrossEncoderReranker:
    def __init__(self):
        pass  # Will use Ollama for reranking

    async def rerank(self, query: str, candidates: list[SearchResult],
                     top_k: int = 10) -> list[SearchResult]:
        """Score each (query, chunk) pair for relevance."""
        scores = []
        for candidate in candidates:
            score = await self._score_relevance(query, candidate.content)
            scores.append((candidate, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scores[:top_k]]

    async def _score_relevance(self, query: str, chunk: str) -> float:
        """Use Ollama to score relevance 0-1."""
        prompt = f"""Rate the relevance of this code chunk to the query on a scale 0-1.
Query: {query}
Code: {chunk[:500]}
Relevance score (0.0-1.0):"""
        # Call Ollama with small model
        response = await ollama.generate('mistral:7b', prompt)
        return float(response.strip())
```

## Query Augmentation

```python
class QueryAugmenter:
    """Generate multiple search queries from error context."""

    def augment_for_bug_localization(self, error_context: ErrorContext) -> list[str]:
        queries = []

        # 1. Error type + message
        if error_context.error_message:
            queries.append(error_context.error_message)

        # 2. Stacktrace frames
        if error_context.stacktrace:
            frames = self._extract_frames(error_context.stacktrace)
            for frame in frames[:3]:
                queries.append(f"{frame['function']} in {frame['file']}")

        # 3. Function names
        function_names = self._extract_function_names(error_context.stacktrace)
        for fn in function_names[:3]:
            queries.append(f"def {fn}")

        # 4. Error type specific
        error_type = self._classify_error(error_context)
        if error_type == 'NullPointer':
            queries.append("null check None guard")
        elif error_type == 'TypeError':
            queries.append("type conversion validation")
        # ... more error-type templates

        # 5. Description keywords
        if error_context.description:
            queries.append(error_context.description[:200])

        return queries
```

## Similarity Metrics

| Metric | Use Case | pgvector Operator |
|---|---|---|
| Cosine Similarity | Code chunk semantic search | `<=>` (distance) → `1 - distance` |
| L2 Distance | Future: image embeddings | `<->` |
| Inner Product | Future: classification | `<#>` |

## Performance Targets

| Metric | Target | Strategy |
|---|---|---|
| Embedding latency | <500ms for 32 chunks | Batch, async HTTP |
| Indexing throughput | >500 chunks/min | Parallel batched inserts |
| Search latency (10k chunks) | <200ms | IVFFlat index |
| Search latency (100k chunks) | <500ms | HNSW index |
| Recall@10 | >0.85 | Hybrid search + reranking |
| Storage per chunk | ~3KB (text) + 3KB (vector) | ~6KB total |
