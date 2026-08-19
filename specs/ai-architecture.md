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
                  ┌─────────────────┴─────────────────┐
                  │                                   │
                  ▼                                   ▼
         ┌──────────────┐                    ┌──────────────┐
         │ 2. Retrieval  │                    │  3. Bug      │
         │    Engine     │                    │  Localizer   │
         │ (hybrid: vec  │                    │  (rank files)│
         │  + FTS)       │                    │              │
         └──────┬───────┘                    └──────┬───────┘
                │                                   │
                └────────────────┬──────────────────┘
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
         │ 5. Patch      │                    │  7. Report    │
         │ Generator     │                    │  Generator    │
         │ (V1)          │                    │              │
         └──────┬───────┘                    └──────────────┘
                │
                ▼
         ┌──────────────┐
         │ 6. Validation │   ← STUB (not wired in pipeline)
         │ Agent         │
         └──────────────┘
```

**Communication**: the Django backend calls the ai-engine over **plain HTTP** (httpx, 300s timeouts) at `AI_ENGINE_URL` (default `http://ai-engine:8002`). **No gRPC.** The ai-engine is a FastAPI server that wraps per-step agents.

## Agent Specifications

### Indexing (shared responsibility)

| Property | Value |
|---|---|
| **Purpose** | Parse repository into semantic chunks + embeddings |
| **Where it runs** | Tree-sitter chunking in **Django** (`repositories/chunking.py`, `repositories/tasks.py`); embeddings via ai-engine `/embed` |
| **Model** | `nomic-embed-text` via Ollama (768-dim) |
| **Batch size** | 32 chunks per request |
| **Storage** | pgvector `ChunkEmbedding` with **HNSW** index |

**Algorithm** (Django side):
```
1. Clone/pull repository via GitService
2. Walk directory tree; filter by IGNORED_DIRS / IGNORED_EXTENSIONS
3. For each file: read content, decode, split into semantic chunks
4. Store CodeChunk rows (content, start_line, end_line, chunk_type, metadata)
5. Batch-embed via ai-engine /embed (nomic-embed-text, 768-dim)
6. Store vectors in ChunkEmbedding (HNSW index)
7. Build repo summary (JSONB)
```

### Agent: Log Analyzer

| Property | Value |
|---|---|
| **Endpoint** | `POST /analyze-logs` |
| **Purpose** | Parse and structure error input for search |
| **Input** | ErrorContext (stacktrace, logs, description) |
| **Output** | Structured queries + metadata |
| **Model** | Tier-configured (qwen2.5-coder 3b/7b/14b) |

### Agent: Retrieval Engine

| Property | Value |
|---|---|
| **Purpose** | Retrieve relevant code chunks for a given query |
| **Input** | Query text, repository_id, top_k |
| **Output** | Ranked list of (chunk_id, score, content, file_path) |
| **Model** | None (vector search + FTS) |
| **Tools** | pgvector (HNSW), PostgreSQL FTS (tsvector), pg_trgm |
| **Location** | `agents/retrieval_engine/engine.py` |

Hybrid search combines cosine similarity over embeddings with keyword FTS; scores are merged and files ranked by suspicion.

### Agent: Bug Localizer

| Property | Value |
|---|---|
| **Endpoint** | `POST /localize-bug` |
| **Purpose** | Rank files by probability of containing the bug |
| **Input** | Repository ID, ErrorContext, log analysis queries |
| **Output** | Ordered list of SuspiciousFile with scores and evidence |
| **Model** | None (heuristic scoring + retrieval) |
| **Location** | `agents/bug_localizer/localizer.py` |

**Scoring**: aggregate chunk scores per file, boost files appearing in the stacktrace and files whose line ranges match reported line numbers, normalize to [0,1].

### Agent: Root Cause Agent

| Property | Value |
|---|---|
| **Endpoint** | `POST /analyze-root-cause` |
| **Purpose** | Generate detailed root cause analysis |
| **Input** | ErrorContext, log analysis, suspicious files, code context |
| **Output** | Structured RCA (summary, root_file, root_line, cause_chain, confidence, reasoning) |
| **Model** | Tier-configured LLM via Ollama (temperature 0, strict JSON) |
| **Location** | `agents/root_cause/rca_agent.py` |

### Agent: Patch Generator

| Property | Value |
|---|---|
| **Endpoint** | `POST /suggest-fix` |
| **Purpose** | Generate a candidate patch to fix the identified bug |
| **Input** | RCA result, full code of root file, error context |
| **Output** | Unified diff + AI-ready fix plan + explanation |
| **Model** | Tier-configured LLM via Ollama |
| **Guardrail** | Never touches test files; minimal changes |

### Agent: Validation Agent

| Property | Value |
|---|---|
| **Endpoint** | none (stub) |
| **Status** | **NOT WIRED** — `agents/validation_agent/validator.py` returns `not_implemented` |
| **Purpose (future)** | Run tests and static analysis on the generated patch in an isolated sandbox |
| **Deferred** | Sandbox validation container is a stub; not part of the pipeline |

### Agent: Report Generator

| Property | Value |
|---|---|
| **Endpoint** | `POST /generate-report` |
| **Purpose** | Compile a comprehensive final report |
| **Input** | All analysis results (localization, RCA, patch) |
| **Output** | Multi-section markdown report |
| **Model** | Tier-configured LLM via Ollama; robust to disabled/missing stages |

## Ollama Model Strategy

| Tier | Label | Models | Params |
|---|---|---|---|
| `fast` | Fast | qwen2.5-coder:3b | 3.1B |
| `balanced` | Balanced | qwen2.5-coder:7b | 7.6B |
| `precise` | Precise | qwen2.5-coder:14b | 14.8B |

Embeddings: `nomic-embed-text` (137M, 768-dim).

The active tier is a **PlatformSetting** configurable via admin (`/api/v1/auth/admin/model-settings/`). Per-stage pipeline toggles are also available in admin.

## Input Limits & Safety

- ai-engine rejects payloads over **200k chars** on the analysis endpoints (400) — bounds prompt-injection surface and runaway costs.
- All LLM calls use **temperature 0** and strict JSON output with tolerant parsing (`agents/json_utils.py`).

## Agent Communication Protocol

```
Internal:
  FastAPI routes → per-agent modules (single process)
  Django orchestrator calls each endpoint synchronously over HTTP
  Celery task chaining drives the pipeline

No gRPC. No NATS/RabbitMQ. No OpenTelemetry.
```