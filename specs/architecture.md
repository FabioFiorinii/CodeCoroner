# CodeCoroner — Architecture Diagram

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐    │
│  │ React SPA   │  │ REST Client │  │ Git CLI      │  │ CI/CD Hook │    │
│  │ (Dashboard)  │  │ (curl/httpie)│  │ (git push hook)│  │ (GH Action) │    │
│  └──────┬──────┘  └──────┬───────┘  └──────┬────────┘  └──────┬───────┘    │
│         │                │                 │                 │              │
└─────────┼────────────────┼─────────────────┼─────────────────┼──────────────┘
          │                │                 │                 │
          ▼                ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY (Django)                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │                        Nginx / Caddy                                    ││
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
│  │  │ patches    │ │ reports      │ │ webhooks     │ │ celery_tasks  │ │   │
│  │  │ (patch mgmt│ │ (RCA docs,   │ │ (integrations)│ │ (task status)│ │   │
│  │  │  validation)│ │  final)      │ │              │ │              │ │   │
│  │  └────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Services Layer                                 │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐   │   │
│  │  │ GitService   │ │ IndexService │ │ AnalyseSvc │ │ PatchSvc   │   │   │
│  │  │ (clone/fetch)│ │ (chunk/store)│ │ (orchestra)│ │ (generate)  │   │   │
│  │  └──────────────┘ └──────────────┘ └────────────┘ └────────────┘   │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │ ReportSvc    │ │ SandboxSvc   │ │ EvalSvc      │                 │   │
│  │  │ (generate    │ │ (podman exec)│ │ (test/static) │                 │   │
│  │  │  doc)        │ │              │ │              │                 │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       Task Queue (Celery)                            │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │   │
│  │  │ Index Task   │ │ Analyse Task │ │ Patch Task   │ │ Report Task│ │   │
│  │  │ (async index)│ │ (multi-step) │ │ (gen+test)   │ │ (finalize) │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │   │
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
│  │                         AI Agents (Python)                             │  │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │  │
│  │  │ Repository     │ │ Log Analyzer   │ │ Bug Localizer  │             │  │
│  │  │ Indexer        │ │ (parse logs,   │ │ (retrieve code │             │  │
│  │  │ (tree-sitter)  │ │  correlate)    │ │  + rank files) │             │  │
│  │  └────────────────┘ └────────────────┘ └────────────────┘             │  │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │  │
│  │  │ Root Cause     │ │ Patch Generator│ │ Validation     │             │  │
│  │  │ Agent          │ │ (diff gen)     │ │ Agent          │             │  │
│  │  │ (RCA chain)    │ │                │ │ (test+static)  │             │  │
│  │  └────────────────┘ └────────────────┘ └────────────────┘             │  │
│  │  ┌────────────────┐ ┌────────────────┐                                │  │
│  │  │ Report         │ │ Embedding      │                                │  │
│  │  │ Generator      │ │ Generator      │                                │  │
│  │  │ (doc gen)      │ │ (chunk→vec)    │                                │  │
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
│  │   ├─ Embeddings (vec)   │  │  ├─ Cache (API resp)   │                     │
│  │   ├─ Vector indexes     │  │  └─ Session store      │                     │
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
│  │  :8080       │    │  :8000       │    │  :5432       │                  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘                  │
│                             │                      │                       │
│                             │              ┌──────────────┐                │
│                             │              │  pgadmin     │                │
│                             │              │  optional    │                │
│                             │              └──────────────┘                │
│                             ▼                                              │
│                      ┌──────────────┐    ┌──────────────┐                 │
│                      │  redis       │    │  celery_worker│                 │
│                      │  :6379       │    │  (scalable)   │                 │
│                      └──────────────┘    └──────┬────────┘                 │
│                                                  │                         │
│                                                  ▼                         │
│                      ┌──────────────┐    ┌──────────────┐                 │
│                      │  ollama      │    │  sandbox      │                 │
│                      │  :11434      │    │  (ephemeral)  │                 │
│                      └──────────────┘    └──────────────┘                 │
│                                                  │                         │
│                                                  ▼                         │
│                      ┌──────────────┐    ┌──────────────┐                 │
│                      │  minio       │    │  ai-engine    │                 │
│                      │  (artifacts) │    │  (agents)     │                 │
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
  ├── Step 1: IndexRepository
  │   ├── Check if repo already indexed
  │   ├── If not: clone/fetch via GitService
  │   ├── Parse AST via Tree-sitter (ai-engine)
  │   ├── Chunk semantically
  │   ├── Generate embeddings (Ollama)
  │   └── Store in pgvector
  │
  ├── Step 2: AnalyzeInput
  │   ├── Parse logs/stacktrace via LogAnalyzer
  │   ├── Extract frames, error types, line numbers
  │   └── Build search queries
  │
  ├── Step 3: BugLocalization
  │   ├── Hybrid search (pgvector + tsvector)
  │   ├── Rerank results
  │   ├── Score files by suspicion
  │   └── Return Top-N candidate files
  │
  ├── Step 4: RootCauseAnalysis
  │   ├── Retrieve full context for candidate files
  │   ├── Build Ollama prompt with error + code context
  │   ├── Generate RCA reasoning chain
  │   └── Store RCA result
  │
  └── Step 5: ReportGeneration
      ├── Format RCA + localization data
      ├── Generate structured report
      ├── Update AnalysisRun (status=completed)
      └── Notify via WebSocket
```

## Deployment Architecture (MVP)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Single Host (MVP)                                │
│                                                                         │
│  Host: Ubuntu 24.04 / Fedora 40                                        │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Podman Compose                               │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │   │
│  │  │ Reverse    │  │ Django     │  │ Celery     │  │ PostgreSQL │  │   │
│  │  │ Proxy/SSL  │  │ (gunicorn) │  │ Worker(s)  │  │ + pgvector  │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │   │
│  │  │ Redis      │  │ Ollama     │  │ MinIO      │  │ AI Engine  │  │   │
│  │  │            │  │ (GPU if    │  │ (blob      │  │ (agents)   │  │   │
│  │  │            │  │  avail)    │  │  store)    │  │            │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Volumes:                                                               │
│    pg_data        - PostgreSQL persistent storage                       │
│    redis_data     - Redis persistence                                   │
│    minio_data     - Artifact storage (patches, reports)                 │
│    ollama_models  - Ollama model weights                                │
│    repo_cache     - Cloned repositories                                 │
│    static_volume  - Django collected static files                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Communication Patterns

| Pattern | Protocol | Use Case |
|---|---|---|
| REST (DRF) | HTTP/JSON | CRUD operations, analysis submission |
| WebSocket | ASGI (Daphne) | Real-time status updates |
| Celery Tasks | Redis/AMQP | Async pipeline execution |
| gRPC (future) | HTTP/2 + protobuf | Agent-to-agent communication |
| Ollama API | HTTP/JSON (localhost) | LLM inference, embeddings |

## Scalability Characteristics

| Dimension | MVP Strategy | Future Strategy |
|---|---|---|
| **Concurrent analyses** | Single Celery worker, queue | Multiple workers, priority queues |
| **Repository size** | <100MB repos, partial index | Streaming index, incremental |
| **Vector search** | Brute force (pgvector) | IVFFlat → HNSW indexes |
| **LLM throughput** | Ollama single model | Model sharding, multiple Ollama nodes |
| **Storage** | Monolithic PostgreSQL | Read replicas, sharded chunks |
| **Frontend** | Single React SPA | SSR (Next.js), CDN caching |
