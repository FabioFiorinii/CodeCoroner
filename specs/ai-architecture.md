# CodeCoroner — AI Architecture

## Agent System Overview

```
                        ┌─────────────────────────┐
                        │    Error Context In      │
                        │  (logs, stacktrace, etc) │
                        └───────────┬─────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │   1. Log Analyzer        │
                        │   Parse & structure input│
                        └───────────┬─────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                  │
                  ▼                 ▼                  ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ Repository    │  │ Embedding     │  │ Retrieval    │
         │ Indexer       │  │ Generator     │  │ Engine       │
         │ (tree-sitter) │  │ (Ollama)      │  │ (hybrid)     │
         └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                │                 │                  │
                └─────────────────┼──────────────────┘
                                  │
                                  ▼
                        ┌─────────────────────────┐
                        │   3. Bug Localizer       │
                        │   Rank suspicious files  │
                        └───────────┬─────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │   4. Root Cause Agent    │
                        │   Generate RCA chain     │
                        └───────────┬─────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  │                                   │
                  ▼                                   ▼
         ┌──────────────┐                    ┌──────────────┐
         │ 5. Patch      │                    │ 8. Report     │
         │ Generator     │                    │ Generator     │
         │ (V1)          │                    │               │
         └──────┬───────┘                    └──────────────┘
                │
                ▼
         ┌──────────────┐
         │ 6. Validation │
         │ Agent         │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ 7. Evaluation │
         │ Agent         │
         └──────────────┘
```

## Agent Specifications

### Agent 1: Repository Indexer

| Property | Value |
|---|---|
| **Purpose** | Parse repository into code graph and semantic chunks |
| **Input** | Repository path, language list |
| **Output** | List of IndexedFile + List of CodeChunk |
| **Model** | None (rule-based + Tree-sitter) |
| **Tools** | `tree-sitter` parsers, `git` CLI |
| **Success metric** | 100% files parsed without error; coverage >95% of code |

**Prompt**: N/A — rule-based AST parsing via Tree-sitter.

**Algorithm**:
```
1. Walk repository directory tree
2. Filter by supported extensions
3. For each file:
   a. Read content
   b. Hash content (SHA-256)
   c. Check hash against last indexed → skip if unchanged
   d. Parse AST via Tree-sitter
   e. Extract nodes: functions, classes, methods, imports
   f. Split into semantic chunks:
      - Each function → one chunk
      - Each class → one chunk
      - Each method → one chunk
      - Module-level imports → one chunk
      - Module docstring → one chunk
      - Remaining code → block chunks (max 100 lines)
   g. For each chunk: store content, start_line, end_line, chunk_type, metadata
4. Build call graph from import statements and function calls
5. Store call_graph as JSONB on repository
```

### Agent 2: Embedding Generator

| Property | Value |
|---|---|
| **Purpose** | Convert code chunks into vector embeddings |
| **Input** | List of (chunk_id, content, chunk_type) |
| **Output** | List of (chunk_id, embedding_vector) |
| **Model** | `nomic-embed-text` via Ollama (768-dim) |
| **Tools** | `httpx` → Ollama API `/api/embeddings` |
| **Success metric** | Throughput >100 chunks/min; embedding quality within 95% of OpenAI ada-002 |
| **Batch size** | 32 chunks per request |

**Prompt structure**:
```
System: You are a code embedding generator.
For each code snippet, generate a vector embedding
that captures semantic meaning including:
- Function/class purpose
- Control flow patterns
- Error handling
- Data flow

Prefix each chunk with a type indicator:
- "function: " for functions
- "class: " for classes
- "method: " for methods
- "code: " for generic blocks

Chunk: {{content}}
```

**Implementation**:
```python
class EmbeddingGenerator:
    def __init__(self, ollama_base_url: str = "http://ollama:11434"):
        self.client = httpx.AsyncClient(base_url=ollama_base_url)
        self.model = "nomic-embed-text"
        self.batch_size = 32

    async def generate_batch(self, chunks: list[CodeChunk]) -> list[tuple[str, list[float]]]:
        texts = [self._format_chunk(c) for c in chunks]
        response = await self.client.post("/api/embeddings", json={
            "model": self.model,
            "input": texts
        })
        data = response.json()
        return [(chunks[i].id, data["embeddings"][i]) for i in range(len(chunks))]

    def _format_chunk(self, chunk: CodeChunk) -> str:
        prefix_map = {
            'function': 'function',
            'class': 'class',
            'method': 'method',
            'block': 'code',
            'module': 'module',
            'docstring': 'docstring',
        }
        return f"{prefix_map.get(chunk.chunk_type, 'code')}: {chunk.content}"
```

### Agent 3: Retrieval Engine

| Property | Value |
|---|---|
| **Purpose** | Retrieve relevant code chunks for a given query |
| **Input** | Query text, repository_id, top_k (default 20) |
| **Output** | Ranked list of (chunk_id, score, content, file_path) |
| **Model** | None (vector search + BM25) |
| **Tools** | pgvector (IVFFlat), PostgreSQL FTS (tsvector), pg_trgm |
| **Success metric** | Recall@10 >0.85; latency <500ms |

**Hybrid Search Strategy**:
```sql
-- Hybrid search query (Python-built)
WITH semantic AS (
    SELECT
        c.id,
        c.content,
        c.file_id,
        1 - (ce.embedding <=> :query_embedding) AS score,
        'semantic' AS match_type
    FROM code_chunks c
    JOIN chunk_embeddings ce ON ce.chunk_id = c.id
    WHERE 1 - (ce.embedding <=> :query_embedding) > :semantic_threshold
    ORDER BY score DESC
    LIMIT :semantic_k
),
keyword AS (
    SELECT
        c.id,
        c.content,
        c.file_id,
        ts_rank(to_tsvector('english', c.content), :query_tsquery) AS score,
        'keyword' AS match_type
    FROM code_chunks c
    WHERE to_tsvector('english', c.content) @@ :query_tsquery
    ORDER BY score DESC
    LIMIT :keyword_k
)
SELECT id, content, file_id, score, match_type FROM semantic
UNION ALL
SELECT id, content, file_id, score, match_type FROM keyword
WHERE id NOT IN (SELECT id FROM semantic)
ORDER BY score DESC
LIMIT :top_k;
```

**Reranking** (Cross-encoder):
```
After initial retrieval, rerank top 50 results using a cross-encoder.
For MVP: use Ollama LLM to score relevance as 0/1.
For V1: deploy a dedicated cross-encoder model (e.g., cross-encoder/ms-marco-MiniLM-L-6-v2).
```

### Agent 4: Log Analyzer

| Property | Value |
|---|---|
| **Purpose** | Parse and structure error input for search |
| **Input** | ErrorContext (stacktrace, logs, description) |
| **Output** | Structured queries + metadata |
| **Model** | `deepseek-coder` or `mistral` via Ollama |
| **Tools** | Regex patterns, Ollama LLM |
| **Success metric** | Extracts correct error type 95%; identifies all file paths in stacktrace |

**Prompt**:
```
System: You are a log and stacktrace analyzer for software debugging.
Analyze the provided error context and extract structured information.

Input:
<error_context>
{{error_context}}
</error_context>

Extract and output ONLY valid JSON with these fields:
1. error_type: The type/category of error (e.g., NullPointerException, TypeError, IndexError)
2. error_message: The main error message
3. file_paths: List of file paths mentioned in stacktrace (in order)
4. line_numbers: List of line numbers mentioned
5. key_functions: Function names in the call stack
6. library_frames: Frames from external libraries (filtered)
7. application_frames: Frames from the user's code
8. search_queries: Array of 3-5 search strings to find relevant code:
   - Query 1: Most specific (function + error)
   - Query 2: Error context
   - Query 3: File/module names
   - Query 4: Data types involved
   - Query 5: General description
9. confidence: How confident you are in the analysis (0.0-1.0)

Output ONLY valid JSON, no other text.
```

### Agent 5: Bug Localizer

| Property | Value |
|---|---|
| **Purpose** | Rank files by probability of containing the bug |
| **Input** | Repository ID, ErrorContext, parsed queries from LogAnalyzer |
| **Output** | Ordered list of SuspiciousFile with scores and evidence |
| **Model** | None (heuristic scoring + retrieval) |
| **Tools** | Retrieval Engine, File scoring algorithm |
| **Success metric** | Bug in Top-3 files >80%; Top-1 >50% |

**Scoring Algorithm**:
```python
class BugLocalizer:
    def localize(self, repo_id: str, error_context: dict,
                 log_analysis: dict) -> list[SuspiciousFile]:
        # 1. Extract search queries from log analysis
        queries = log_analysis['search_queries']

        # 2. For each query, run hybrid retrieval
        all_chunks = []
        for query in queries:
            chunks = self.retrieval_engine.search(
                query=query,
                repo_id=repo_id,
                top_k=20
            )
            all_chunks.extend(chunks)

        # 3. Aggregate scores by file
        file_scores = defaultdict(lambda: {
            'score': 0.0,
            'matched_lines': set(),
            'chunks': []
        })

        for chunk in all_chunks:
            file_path = chunk['file_path']
            file_scores[file_path]['score'] += chunk['score']
            file_scores[file_path]['matched_lines'].update(
                range(chunk['start_line'], chunk['end_line'] + 1)
            )
            file_scores[file_path]['chunks'].append(chunk)

        # 4. Apply heuristics
        stacktrace_files = set(log_analysis.get('application_frames', []))
        stacktrace_lines = set(log_analysis.get('line_numbers', []))

        for file_path, data in file_scores.items():
            # Boost files in stacktrace
            if any(sf in file_path for sf in stacktrace_files):
                data['score'] *= 1.5
            # Boost files with matching line numbers
            if data['matched_lines'].intersection(stacktrace_lines):
                data['score'] *= 1.3
            # Boost recently modified files (optional)
            # data['score'] *= self._recency_boost(file_path)

        # 5. Sort by score descending
        ranked = sorted(
            file_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )

        # 6. Normalize scores to [0, 1]
        max_score = ranked[0][1]['score'] if ranked else 1.0

        results = []
        for rank, (file_path, data) in enumerate(ranked[:10], 1):
            results.append(SuspiciousFile(
                file_path=file_path,
                suspicion_score=round(data['score'] / max_score, 4),
                matched_lines=sorted(data['matched_lines']),
                evidence=self._build_evidence(data['chunks']),
                rank=rank
            ))

        return results
```

### Agent 6: Root Cause Agent

| Property | Value |
|---|---|
| **Purpose** | Generate detailed root cause analysis |
| **Input** | ErrorContext, LogAnalysis, SuspiciousFiles list, full code of top files |
| **Output** | Structured RCA (summary, root_file, root_line, cause_chain, reasoning) |
| **Model** | `deepseek-coder:14b` or `codellama:13b` via Ollama |
| **Tools** | Ollama LLM, Code context retrieval |
| **Success metric** | RCA judged "plausible" by human >70%; root_file correct >60% |

**Prompt**:
```
System: You are an expert software engineer performing Root Cause Analysis.
Analyze the bug report and code context to identify the root cause.

Error Context:
<error_context>
{{error_context}}
</error_context>

Log Analysis:
<log_analysis>
{{log_analysis}}
</log_analysis>

Most Suspicious Files (ranked by suspicion score):
<suspicious_files>
{{suspicious_files}}
</suspicious_files>

Full Code of Top Files:
<code_context>
{{code_context}}
</code_context>

Perform a thorough root cause analysis:

1. TRACE THE ERROR: Walk through the call chain from the error point backwards.
2. IDENTIFY THE ROOT: Determine the origin of the defect — not where it manifests,
   but where the incorrect state/logic originates.
3. ANALYZE THE DATA FLOW: How did incorrect data propagate to cause the error?
4. CONSIDER EDGE CASES: Null values, race conditions, incorrect assumptions,
   missing validation, off-by-one errors.
5. PROVIDE EVIDENCE: Cite specific lines of code that support your conclusion.

Output ONLY valid JSON:
{
  "summary": "One-line summary of the root cause",
  "root_file": "Path to the file containing the root cause",
  "root_line": <integer line number or null>,
  "cause_chain": "Step-by-step explanation of how the bug propagates",
  "confidence": <float 0.0-1.0>,
  "reasoning": "Detailed reasoning with code references",
  "evidence_chunks": ["chunk_id_1", "chunk_id_2"],
  "affected_files": ["path/to/file1", "path/to/file2"],
  "suggested_fix_type": "null_check | validation | logic_fix | refactor | other",
  "severity": "critical | major | minor | cosmetic"
}
```

### Agent 7: Patch Generator (V1)

| Property | Value |
|---|---|
| **Purpose** | Generate a candidate patch to fix the identified bug |
| **Input** | RCA result, full code of root file, error context |
| **Output** | Git diff patch |
| **Model** | `deepseek-coder:14b` via Ollama |
| **Tools** | Ollama LLM |
| **Success metric** | Patch compiles/lint-passes >80%; tests pass >50% |

**Prompt**:
```
System: You are an expert software engineer tasked with generating a bug fix patch.

Root Cause Analysis:
<rca>
{{rca}}
</rca>

Current Code (file: {{root_file}}):
<code>
{{file_content}}
</code>

Error Context:
<error_context>
{{error_context}}
</error_context>

Generate a minimal, correct patch that fixes the root cause.
Requirements:
1. Make minimal changes — only fix the actual bug
2. Follow the existing code style
3. Handle edge cases (nulls, empty, bounds)
4. Add defensive checks where appropriate
5. The patch MUST be a valid git diff format

Output ONLY valid JSON:
{
  "patch": "```diff\n--- a/{{root_file}}\n+++ b/{{root_file}}\n@@ -... +... @@\n ...\n```",
  "summary": "Brief description of the fix",
  "modified_files": ["{{root_file}}"],
  "confidence": <float 0.0-1.0>,
  "explanation": "Why this fix addresses the root cause"
}
```

### Agent 8: Validation Agent (V1)

| Property | Value |
|---|---|
| **Purpose** | Run tests and static analysis on the generated patch |
| **Input** | Patch diff, repository ID |
| **Output** | Validation result with scores |
| **Model** | None (rules-based execution) |
| **Tools** | Podman sandbox, pytest, ruff, mypy |
| **Success metric** | Validation completes in <5 min; reproducible results |

**Algorithm**:
```
1. Create sandbox container from repository image
2. Apply patch to repository files
3. Run static analysis:
   a. ruff . --output-format=json (collect errors, warnings)
   b. mypy . (collect type errors)
4. Run test suite:
   a. pytest -x --tb=short -q (collect pass/fail/skip)
5. Score:
   - Test pass rate: (passed / total) * 0.6
   - Lint score: max(0, 1 - (errors * 0.1 + warnings * 0.02)) * 0.2
   - Type score: max(0, 1 - type_errors * 0.1) * 0.2
   - Overall = test_score + lint_score + type_score
```

### Agent 9: Report Generator

| Property | Value |
|---|---|
| **Purpose** | Compile a comprehensive final report |
| **Input** | All analysis results (localization, RCA, patch, validation) |
| **Output** | Structured report in markdown |
| **Model** | `mistral` via Ollama for narrative generation |
| **Tools** | Ollama LLM + Jinja2 templates |
| **Success metric** | Report is complete; covers all sections; human-readable |

**Template**:
```markdown
# Bug Analysis Report

## Summary
{{summary}}

## Error Context
- **Error Type**: {{error_type}}
- **Message**: {{error_message}}
- **Environment**: {{environment}}

## Bug Localization
### Top Suspicious Files
| Rank | File | Score | Matched Lines |
|------|------|-------|---------------|
{% for file in suspicious_files %}
| {{file.rank}} | `{{file.file_path}}` | {{file.score}} | {{file.lines}} |
{% endfor %}

## Root Cause Analysis
### Root File
`{{root_file}}` line {{root_line}}

### Cause Chain
{{cause_chain}}

### Reasoning
{{reasoning}}

## Patch
{{#if patch}}
### Summary
{{patch_summary}}

### Diff
```diff
{{patch_diff}}
```

### Validation
- Tests passed: {{tests_passed}}/{{tests_total}}
- Lint errors: {{lint_errors}}
- Type errors: {{type_errors}}
- Overall score: {{overall_score}}
{{/if}}

## Recommendations
{{recommendations}}
```

## Ollama Model Strategy

| Use Case | Model | Size | RAM | Quality |
|---|---|---|---|---|
| Code Embeddings | `nomic-embed-text` | 137M | ~1GB | Excellent |
| Log Analysis | `mistral:7b` | 7B | ~8GB | Good |
| Bug Localization | `deepseek-coder:6.7b` | 6.7B | ~8GB | Very Good |
| Root Cause Analysis | `deepseek-coder:14b` | 14B | ~16GB | Excellent |
| Patch Generation | `deepseek-coder:14b` | 14B | ~16GB | Excellent |
| Report Generation | `mistral:7b` | 7B | ~8GB | Good |
| Reranking (V1) | `mxbai-embed-large` | 334M | ~2GB | Good |

## Agent Communication Protocol

```
Internal:
  Python function calls (single process)
  JSON serialization between steps
  Celery task chaining for pipeline

External (future):
  gRPC for agent-to-agent streaming
  NATS / RabbitMQ for event broadcasting
  OpenTelemetry for tracing across agents
```
