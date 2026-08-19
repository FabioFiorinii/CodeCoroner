# CodeCoroner — Architecture Diagram

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐                      │
│  │ React SPA   │  │ REST Client │  │ Git CLI      │                      │
│  │ (Dashboard)  │  │ (curl/httpie)│  │ (git push hook)│                      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬────────┘                      │
│         │                │                 │                               │
└─────────┼────────────────┼─────────────────┼──────────────────────────────┘
          │                │                 │
          ▼                ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY (Nginx)                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │  TLS termination :8443 (self-signed, auto-generated on first start)      ││
│  │  HTTP :8080 → 301 redirect to HTTPS                                       ││
│  │  Security headers + CSP (HSTS opt-in via ENABLE_HSTS=true)               ││
│  │  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐ ││
│  │  │ Auth     │  │ DRF Router  │  │ WebSocket  │  │ Static Files    │ ││
│  │  │ (JWT)   │  │ /api/v1/    │  │ /ws/       │  │ /assets/        │ ││
│  │  └──────────┘  └──────┬───────┘  └────────────┘  └──────────────────┘ ││
│  └──────────────────────┼───────────────────────────────────────────────────┘│
└─────────────────────────┼────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER (Django)                          │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Django Apps                                 │   │
│  │  ┌────────────┐ ┌──────────────┐ ┌──────────┐ ┌────────────────┐  │   │
│  │  │ accounts   │ │ projects     │ │ analysis  │ │ repositories   │  │   │
│  │  │ (users,    │ │ (crud,       │ │ (workflows,│ │ (git mgmt,     │  │   │
│  │  │  auth)     │ │  config)     │ │  results) │ │  indexing)     │  │   │
│  │  └────────────┘ └──────────────┘ └──────────┘ └────────────────┘  │   │
│  │  ┌────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │   │
│  │  │ patches    │ │ reports      │ │ webhooks     │ │ common       │ │   │
│  │  │ (patch mgmt│ │ (RCA docs,   │ │ (integrations)│ │ (logging,    │ │   │
│  │  │  validation)│ │  final)      │ │              │ │  cleanup)    │ │   │
│  │  └────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Services Layer                                 │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐   │   │
│  │  │ GitService   │ │ IndexService │ │ AnalyseSvc │ │ PatchSvc   │   │   │
│  │  │ (clone/fetch)│ │ (chunk/store)│ │ (orchestra)│ │ (generate)  │   │   │
│  │  └──────────────┘ └──────────────┘ └────────────┘ └────────────┘   │   │
│  │  ┌──────────────┐ ┌──────────────┐                                │   │
│  │  │ ReportSvc    │ │ DLQ/Logging  │                                │   │
│  │  │ (generate    │ │ (cleanup,    │                                │   │
│  │  │  doc)        │ │  dead-letter) │                                │   │
│  │  └──────────────┘ └──────────────┘                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       Task Queue (Celery)                            │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │   │
│  │  │ Index Task   │ │ Analyse Task │ │ Webhook Task │ │ Purge Task │ │   │
│  │  │ (async index)│ │ (multi-step) │ │ (dispatch)   │ │ (weekly)   │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │   │
│  │  Queue routing: 'llm' for analyses, 'celery' for others             │   │
│  │  acks_late + reject_on_worker_lost; DLQ for exhausted retries       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI ENGINE LAYER                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                     Ollama Server (localhost:11434)                    │  │
│  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐               │  │
│  │  │ CodeLlama /   │ │ Nomic Embed   │ │ Mistral       │               │  │
│  │  │ DeepSeek-Coder│ │ Text (embed)  │ │ (RCA gen)     │               │  │
│  │  └───────────────┘ └───────────────┘ └───────────────┘               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Agent Server (port 8002)                    │  │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │  │
│  │  │ Log Analyzer   │ │ Bug Localizer  │ │ Root Cause     │             │  │
│  │  │ (parse logs,   │ │ (hybrid search │ │ Agent          │             │  │
│  │  │  correlate)    │ │  + scoring)    │ │ (RCA chain)    │             │  │
│  │  └────────────────┘ └────────────────┘ └────────────────┘             │  │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │  │
│  │  │ Patch Generator│ │ Report         │ │ Validation     │             │  │
│  │  │ (diff gen)     │ │ Generator      │ │ Agent (stub)   │             │  │
│  │  └────────────────┘ └────────────────┘ └────────────────┘             │  │
│  │  ┌────────────────┐ ┌────────────────┐                                │  │
│  │  │ Embedding      │ │ Index          │                                │  │
│  │  │ Generator      │ │ (chunk→vec)    │                                │  │
│  │  └────────────────┘ └────────────────┘                                │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                           │
│                                                                             │
│  ┌────────────────────────┐  ┌────────────────────────┐                     │
│  │   PostgreSQL + pgvector │  │       Redis            │                     │
│  │   ├─ Operational data   │  │  ├─ Celery broker      │                     │
│  │   ├─ Code chunks        │  │  ├─ Celery result back │                     │
│  │   ├─ Embeddings (768-d) │  │  ├─ Cache (API resp)   │                     │
│  │   ├─ HNSW vector index  │  │  └─ Session store      │                     │
│  │   └─ Full text search   │  │                        │                     │
│  │   (tsvector)            │  │                        │                     │
│  │                         │  │                        │                     │
│  │   Extensions:           │  │                        │                     │
│  │   ├─ pgvector           │  │                        │                     │
│  │   └─ pg_trgm            │  │                        │                     │
│  └────────────────────────┘  └────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Container Architecture (Podman Compose)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PODMAN NETWORK (codecoroner_net)                     │
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  nginx       │───▶│  django      │───▶│  postgres    │                  │
│  │  :8080/8443  │    │  :8000       │    │  :5432       │                  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘                  │
│                             │                      │                       │
│                             ▼                      ▼                       │
│                      ┌──────────────┐    ┌──────────────┐                 │
│                      │  redis       │    │  celery      │                 │
│                      │  :6379       │    │  worker/beat │                 │
│                      └──────────────┘    └──────────────┘                 │
│                                                  │                         │
│                                                  ▼                         │
│                      ┌──────────────┐    ┌──────────────┐                 │
│                      │  ollama      │    │  ai-engine   │                 │
│                      │  :11434      │    │  :8002       │                 │
│                      └──────────────┘    └──────────────┘                 │
│                                                  │                         │
│                                                  ▼                         │
│                      ┌──────────────┐    ┌──────────────┐                 │
│                      │  minio       │    │  daphne      │                 │
│                      │  :9000/9001  │    │  :8001 (WS)  │                 │
│                      └──────────────┘    └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Request Flow — Analysis Pipeline

```
User
  │
  ├── POST /api/v1/analyses/  { repo_id, error_context }
  │
  ▼
Django API
  │
  ├── Validates input
  ├── Creates AnalysisRun (status=queued)
  ├── Enqueues Celery task: run_analysis_pipeline(analysis_id)
  └── Returns 202 Accepted + polling_url
        │
        ▼
Celery Worker ──▶ run_analysis_pipeline()
  │
  ├── Step 1: IndexRepository (if not indexed)
  │   ├── Check if repo already indexed
  │   ├── If not: clone/fetch via GitService
  │   ├── Parse AST via Tree-sitter (local, not ai-engine)
  │   ├── Chunk semantically
  │   ├── Generate embeddings via ai-engine /embed (Ollama)
  │   └── Store in pgvector (HNSW index)
  │
  ├── Step 2: AnalyzeInput
  │   ├── Parse logs/stacktrace via ai-engine /analyze-logs
  │   ├── Extract frames, error types, line numbers
  │   └── Build search queries
  │
  ├── Step 3: BugLocalization
  │   ├── Hybrid search via ai-engine /localize-bug (pgvector + tsvector)
  │   ├── Score files by suspicion
  │   └── Return Top-N candidate files
  │
  ├── Step 4: RootCauseAnalysis
  │   ├── Retrieve full context for candidate files
  │   ├── Build prompt with error + code context
  │   ├── Generate RCA via ai-engine /analyze-root-cause
  │   └── Store RCA result
  │
  ├── Step 5: FixSuggestion
  │   ├── Generate diff via ai-engine /suggest-fix
  │   └── Store Patch + FixSuggestion
  │
  ├── Step 6: ReportGeneration
  │   ├── Format all results via ai-engine /generate-report
  │   ├── Store Report
  │   └── Update AnalysisRun (status=completed)
  │
  └── Step 7: Notify via WebSocket (real-time)
```

## Deployment Architecture (MVP)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Single Host (MVP)                                │
│                                                                         │
│  Host: Ubuntu 24.04 / Fedora 40 (WSL2 on Windows)                       │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Podman Compose                               │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │   │
│  │  │ Reverse    │  │ Django     │  │ Celery     │  │ PostgreSQL │  │   │
│  │  │ Proxy + TLS│  │ (runserver)│  │ Worker/Beat│  │ + pgvector │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │   │
│  │  │ Redis      │  │ Ollama     │  │ MinIO      │  │ AI Engine  │  │   │
│  │  │            │  │ (CPU only) │  │ (blob      │  │ (FastAPI)  │  │   │
│  │  │            │  │            │  │  store)    │  │            │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │   │
│  │  ┌────────────┐  ┌────────────┐                                │   │
│  │  │ Daphne     │  │ Nginx      │                                │   │
│  │  │ (WS :8001) │  │ (:8080/8443)│                                │   │
│  │  └────────────┘  └────────────┘                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Volumes:                                                               │
│    pg_data        - PostgreSQL persistent storage                       │
│    redis_data     - Redis persistence                                   │
│    minio_data     - Artifact storage (patches, reports)                 │
│    ollama_models  - Ollama model weights                                │
│    repo_cache     - Cloned repositories (read-only shared with ai-engine)│
│    static_volume  - Django collected static files                       │
│    nginx_certs    - Self-signed TLS certs (auto-generated)              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Communication Patterns

| Pattern | Protocol | Use Case |
|---|---|---|
| REST (DRF) | HTTP/JSON | CRUD operations, analysis submission |
| WebSocket | ASGI (Daphne) | Real-time status updates |
| Celery Tasks | Redis | Async pipeline execution |
| Django → AI Engine | HTTP/JSON (httpx) | LLM inference, embeddings, analysis steps |
| Ollama API | HTTP/JSON (localhost) | Model inference, embeddings |
| Nginx → Django | HTTP (with X-Forwarded-Proto) | Reverse proxy + TLS termination |

## Scalability Characteristics

| Dimension | MVP Strategy | Future Strategy |
|---|---|---|
| **Concurrent analyses** | Single Celery worker, queue | Multiple workers, priority queues |
| **Repository size** | <100MB repos, partial index | Streaming index, incremental |
| **Vector search** | HNSW index (pgvector) | HNSW (already), possibly sharded |
| **LLM throughput** | Ollama single model (CPU) | GPU Ollama, model sharding, multiple nodes |
| **Storage** | Monolithic PostgreSQL | Read replicas, sharded chunks |
| **Frontend** | Single React SPA | SSR (Next.js), CDN caching |

## Security & Hardening (Current State)

- TLS termination on nginx (:8443) with self-signed certs; HSTS opt-in
- Security headers (CSP, X-Frame-Options, nosniff, Referrer-Policy) at nginx level
- JWT auth with rotating refresh tokens + blacklist
- Brute-force lockout via django-axes (5 attempts → 1h cooldown)
- Webhook secrets encrypted at rest (Fernet)
- Multi-tenant isolation: project membership, group visibility, owner-only mutations
- Structured JSON logs with daily rotation (prod)
- Dead-letter queue for failed Celery tasks
- Periodic purge: git GC, orphan repo dirs, analysis retention (90d)