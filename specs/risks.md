# CodeCoroner — Technical Risks & Mitigations

## Risk Matrix

| ID | Risk | Probability | Impact | Level | Mitigation |
|---|---|---|---|---|---|
| R1 | LLM hallucinates incorrect root cause | High | High | **Critical** | Confidence scoring, evidence linking, human validation |
| R2 | Embedding quality insufficient for code | Medium | High | **High** | Prefix strategy, hybrid search, reranking |
| R3 | Large repository indexing timeout | High | Medium | **High** | Streaming parser, incremental indexing, time budget |
| R4 | Ollama becomes bottleneck at scale | High | High | **Critical** | Async batching, model quantization, multiple Ollama nodes |
| R5 | Sandbox container escape vulnerability | Low | Critical | **High** | Defense-in-depth: seccomp, no-cap, no-net, read-only |
| R6 | Prompt injection from error context | Medium | High | **High** | Input sanitization, delimiters, output validation |
| R7 | PostgreSQL performance degradation | Medium | High | **High** | HNSW index, read replicas, connection pooling (PgBouncer) |
| R8 | Multi-language AST coverage gaps | Medium | Medium | **Medium** | Graceful fallback: if no parser → line-level chunks |
| R9 | False positives overwhelm users | High | Medium | **High** | Suspicion scoring, threshold tuning, user feedback loop |
| R10 | Celery task queue overload | Medium | Medium | **Medium** | Prioritized queues, concurrency limits, auto-scaling |
| R11 | Git clone for large repos fails/timeout | Medium | Medium | **Medium** | Sparse checkout, shallow clone, size limit enforcement |
| R12 | Model cold start (Ollama load time) | High | Low | **Low** | Keep-alive / pre-warm models on startup |
| R13 | Storage growth (vector + code) | Medium | Medium | **Medium** | Chunk retention policy, old analysis cleanup, S3 lifecycle |
| R14 | WebSocket connection drops | Medium | Low | **Low** | Auto-reconnect with exponential backoff |
| R15 | Cross-encoder reranker unavailable | Low | Medium | **Low** | Fallback to score-only ranking |

## Detailed Risk Analysis

### R1: LLM Hallucination (Critical)

**Description**: LLM generates incorrect root cause analysis, identifying wrong files or incorrect causal chains. This destroys user trust.

**Mitigations**:
1. **Confidence scoring**: Agent outputs 0.0-1.0 confidence; hide low-confidence results
2. **Evidence linking**: Every RCA claim must cite specific code lines (enforced by prompt + validation)
3. **Hybrid retrieval grounds the LLM**: Only present retrieved code chunks, not the full codebase
4. **Human review loop**: MVP adds "Was this analysis helpful?" feedback button
5. **Output validation**: Schema validation ensures required fields; reject malformed outputs
6. **Fallback: return search results only** if confidence < 0.3

### R2: Embedding Quality (High)

**Description**: Code embeddings may not capture semantic meaning well, leading to poor retrieval.

**Mitigations**:
1. **Type prefixing**: Pre-pend "function:", "class:" etc. to embeddings for better separation
2. **Hybrid search**: Combine vector (semantic) + BM25 (keyword) — compensates for weak vectors
3. **Reranking**: Cross-encoder (V1) re-ranks top 50 results for precision
4. **Model selection**: `nomic-embed-text` is specifically trained for code-like embeddings
5. **A/B evaluation**: Compare recall@k against known bug datasets

### R3: Large Repository Indexing (High)

**Description**: Repositories > 500MB or with > 10,000 files cause timeouts and memory issues.

**Mitigations**:
1. **Streaming parser**: Process files one at a time, don't load entire tree into memory
2. **Incremental indexing**: Only re-index changed files (SHA-256 hash)
3. **Shallow clone**: `git clone --depth 1` for MVP
4. **Size limits**: Reject repos > 1GB with clear error message
5. **Time budget**: 30-minute max; kill and report partial indexing
6. **Celery soft/hard time limits**: Prevent worker hang

### R4: Ollama Bottleneck (Critical)

**Description**: Single Ollama instance cannot keep up with embedding + LLM generation demands.

**Mitigations**:
1. **Async HTTP**: Non-blocking httpx client for parallel requests
2. **Batch processing**: Embeddings in batches of 32
3. **Model quantization**: Use GGUF Q4_K_M for 4x speedup
4. **Separate model instances**: Run embedding and generation on different Ollama processes
5. **GPU acceleration**: NVIDIA CUDA passthrough in Podman
6. **Queue management**: Embedding has higher priority than generation (more latency tolerant)
7. **V1: Multiple Ollama replicas**: Load balance behind reverse proxy

### R5: Sandbox Escape (High)

**Description**: Malicious code in repository breaks out of container to host.

**Mitigations** (defense-in-depth):
1. Podman rootless mode (user namespace remapping)
2. Drop all capabilities
3. Custom seccomp profile (whitelist only safe syscalls)
4. Read-only root filesystem
5. No network access
6. No-new-privileges flag
7. Memory limit 2GB, PID limit 100
8. Timeout 5 minutes (SIGKILL if exceeded)
9. Non-root user inside container
10. SELinux labeling (`:Z` volume mounts)
11. Read-only repo mount (`:ro`)
12. Regular security audits

### R9: False Positives (High)

**Description**: Bug localization flags many files that are not actually related, overwhelming users.

**Mitigations**:
1. **Top-K limit**: Return max 10 files
2. **Score threshold**: Minimum 0.2 score to be reported
3. **Score normalization**: Top file always 1.0, others relative
4. **User feedback**: "Mark as not relevant" button to improve over time
5. **Active learning (V2)**: Use feedback to fine-tune scoring weights
6. **A/B evaluation**: Track precision@k, recall@k over time

## Capacity Planning

| Resource | MVP Requirement | Scale Target (100 users) |
|---|---|---|
| PostgreSQL storage | 10 GB | 100 GB |
| Vector storage (1M chunks) | 6 GB | 60 GB |
| Ollama RAM (2 models) | 12 GB | 32 GB (4 models) |
| Worker concurrency | 2 | 8-16 |
| API throughput | 10 req/s | 100 req/s |
| Embedding throughput | 100 chunks/min | 1000 chunks/min |
| LLM generation (sequential) | 1/min | 5/min |
| repo_cache storage | 5 GB | 50 GB |
| MinIO artifacts | 2 GB | 50 GB |

## Technology Risks

| Technology | Risk | Alternative |
|---|---|---|
| pgvector (IVFFlat) | Poor recall with small `lists` | HNSW (pgvector ≥0.5) |
| Celery | Task overhead for small jobs | Dramatiq, Arq, or Redis Queue |
| Tree-sitter | Grammar compilation issues | Fallback to regex/line-based |
| Ollama | CUDA memory fragmentation | vLLM, llama.cpp directly |
| Podman | Volume permission issues | Proper SELinux labeling with `:Z` |
