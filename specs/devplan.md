# CodeCoroner — Development Plan

## Epic Breakdown

```
Epic 1: Foundation & Infrastructure          Week 1-2
Epic 2: Repository Indexing                  Week 3-4
Epic 3: Embeddings & Vector Search           Week 5-6
Epic 4: Bug Localization                     Week 7-8
Epic 5: Root Cause Analysis                  Week 9-10
Epic 6: MVP Frontend & Integration           Week 11-12
Epic 7: Patch Generation                     Month 4
Epic 8: Validation Pipeline                  Month 5
Epic 9: Enterprise Features                  Month 6-7
Epic 10: SaaS Platform                       Month 8+
```

---

## Epic 1: Foundation & Infrastructure

### Feature 1.1: Project Scaffolding

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Initialize backend | `django-admin startproject`, DRF setup, Celery config, ASGI | 1d | None |
| Initialize frontend | Vite + React + TS + Tailwind + shadcn/ui | 1d | None |
| Initialize ai-engine | Python project, modular agents structure | 0.5d | None |
| Podman Compose | Write compose file, Dockerfiles, nginx config | 1d | Backend scaffold |
| Environment config | `.env.example`, settings (base/dev/prod/test) | 0.5d | Backend scaffold |

### Feature 1.2: Authentication

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| User model | Custom `User` with UUID, email unique | 0.5d | 1.1 |
| Register endpoint | `POST /api/v1/auth/register` | 0.5d | User model |
| Login endpoint | `POST /api/v1/auth/login` (JWT) | 0.5d | User model |
| JWT configuration | Access + refresh tokens, rotation | 0.5d | Login endpoint |
| API tokens | Model + CRUD for long-lived tokens | 1d | User model |
| Auth frontend | Login/register pages with form validation | 1d | Auth API |

### Feature 1.3: DevOps Foundation

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| CI pipeline | GitHub Actions: lint, test, build, scan | 1d | 1.1 |
| Pre-commit hooks | ruff, mypy, prettier, secrets detection | 0.5d | 1.1 |
| `Makefile` | Common commands: up, down, test, lint, migrate | 0.5d | 1.1 |

---

## Epic 2: Repository Indexing

### Feature 2.1: Git Service

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Repository model | `Repository` with status tracking | 0.5d | 1.2 |
| Git clone service | Clone via `gitpython`, error handling | 1d | Repository model |
| Git pull service | Incremental update for existing repos | 0.5d | Git clone |
| Celery task | `index_repository_task` async | 0.5d | Git service |

### Feature 2.2: Tree-sitter Integration

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Install tree-sitter | Python bindings, language grammars (Python first) | 0.5d | 2.1 |
| AST parser | Parse file → AST, extract functions/classes | 1d | Tree-sitter |
| Language detection | Map file extension → parser | 0.5d | AST parser |
| Multi-language support | TypeScript, Go, Java, Rust grammars | 2d | AST parser |

### Feature 2.3: Semantic Chunking

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Chunking algorithm | Split AST nodes into CodeChunks | 1.5d | 2.2 |
| Chunk deduplication | Hash-based: skip unchanged chunks | 0.5d | Chunking |
| IndexedFile model | Track per-file index state | 0.5d | 2.1 |
| CodeChunk model | Content, type, line range, metadata | 0.5d | Chunking |

---

## Epic 3: Embeddings & Vector Search

### Feature 3.1: Ollama Integration

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Ollama service client | Async HTTP client for `/api/embeddings`, `/api/generate` | 1d | None (standalone) |
| Model pull automation | `ollama pull nomic-embed-text` in setup script | 0.5d | Ollama service |
| Health checks | Verify Ollama is running + model loaded | 0.5d | Model pull |

### Feature 3.2: Embedding Generation

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| EmbeddingGenerator agent | Batch embedding with prefix strategy | 1d | 3.1 |
| ChunkEmbedding model | pgvector column, model metadata | 0.5d | 2.3 |
| Embedding pipeline | Process chunks → embed → store (Celery batch) | 1d | EmbeddingGenerator |
| Chunk re-embedding | Re-embed only changed chunks | 0.5d | Embedding pipeline |

### Feature 3.3: Search Indexes

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| IVFFlat index | Create index, tune probes | 0.5d | 3.2 |
| FTS index | GIN index on `to_tsvector('english', content)` | 0.5d | 2.3 |
| Trigram index | `pg_trgm` for fuzzy matching | 0.5d | 2.3 |

---

## Epic 4: Bug Localization

### Feature 4.1: Log Analyzer

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| ErrorContext model | Structured input (stacktrace, logs, description) | 0.5d | 1.2 |
| Log Analyzer agent | Parse stacktrace frames, extract error type | 1d | 3.1 |
| Stacktrace frame parser | Regex-based extraction of file:line:function | 0.5d | Log Analyzer |
| Query generation | Generate 3-5 search queries from error context | 0.5d | Log Analyzer |

### Feature 4.2: Hybrid Search

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| HybridSearchEngine | Combine vector + FTS with weighted score | 1.5d | 3.3, 4.1 |
| Query embedding | Embed search query via Ollama | 0.5d | 3.1 |
| Repository filter | Scope search to repository | 0.5d | HybridSearchEngine |
| Performance testing | Benchmark with 1k, 10k, 50k chunks | 0.5d | HybridSearchEngine |

### Feature 4.3: File Scoring

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Scoring algorithm | Aggregate chunk scores by file, apply heuristics | 1d | 4.2 |
| SuspiciousFile model | Store results with score + evidence | 0.5d | 4.2 |
| Bug localization API | `GET /analyses/{id}/localization` | 0.5d | SuspiciousFile model |

---

## Epic 5: Root Cause Analysis

### Feature 5.1: RCA Agent

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Root Cause Agent | Ollama-driven prompt + structured output | 2d | 4.3, 3.1 |
| Code context retrieval | Fetch full source of top suspicious files | 0.5d | 2.1 |
| Prompt engineering | Iterative refinement of RCA prompt | 1d | RCA Agent |
| RootCause model | Store summary, chain, reasoning, confidence | 0.5d | RCA Agent |

### Feature 5.2: RCA Presentation

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| RCA API | `GET /analyses/{id}/root-cause` | 0.5d | 5.1 |
| Evidence linking | Link RCA statements to specific code chunks | 0.5d | 5.1 |
| Confidence scoring | Validate confidence against known bugs | 0.5d | 5.1 |

---

## Epic 6: MVP Frontend

### Feature 6.1: Core Pages

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Layout + navigation | Sidebar, topbar, breadcrumbs, responsive | 1d | 1.1 |
| Dashboard page | Stats cards, recent analyses table, activity chart | 1.5d | 2.1, 4.3 |
| Project list + create | Project cards, new project form | 1d | 1.2 |
| Repository management | Add repo, index button, status badge, file list | 1.5d | 2.1 |
| Analysis submission form | Error context form, validation, submit | 1.5d | 4.3 |

### Feature 6.2: Results Pages

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Status timeline | Live WebSocket updates, step progression, progress bars | 1.5d | 6.1 |
| Bug localization view | Suspicion chart, file list, code viewer with highlights | 2d | 6.1 |
| Root cause view | Cause chain, reasoning markdown, evidence links | 1.5d | 6.1 |
| Report view | Markdown render, export button | 1d | 6.1 |

### Feature 6.3: Polish

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Loading states | Skeleton loaders, spinners | 0.5d | 6.2 |
| Error handling | Error boundaries, toast notifications, retry | 0.5d | 6.2 |
| Empty states | Illustrations + CTAs for empty lists | 0.5d | 6.2 |
| Pagination | Server-side pagination for analyses list | 0.5d | 6.1 |
| Dark mode | Tailwind dark mode support | 0.5d | 6.2 |

---

## Epic 7: Patch Generation (V1)

### Feature 7.1: Patch Agent

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Patch Generator agent | Generate git diff via Ollama | 2d | 5.1 |
| Patch model | Store diff, summary, status | 0.5d | 7.1 |
| Patch API | CRUD for patches | 0.5d | Patch model |

### Feature 7.2: Sandbox Environment

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Sandbox Dockerfile | Multi-language runtime, test tools | 1d | None |
| Sandbox controller | Start container, apply patch, run commands | 1.5d | Sandbox Dockerfile |
| Podman API wrapper | Podman Python SDK: create, exec, cleanup | 1d | Sandbox controller |

### Feature 7.3: Patch Application

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Patch apply in sandbox | Copy repo, apply diff, capture output | 0.5d | 7.2 |
| Test execution | Run pytest in sandbox, collect results | 1d | 7.2 |
| Static analysis | Run ruff + mypy in sandbox | 0.5d | 7.2 |
| Validation scoring | Test pass rate + lint score + type score | 0.5d | Test execution |

---

## Epic 8: Frontend Patch UI (V1)

| Task | Subtasks | Effort | Dependencies |
|---|---|---|---|
| Diff viewer | `react-diff-viewer-continued` integration | 1d | 7.1 |
| Validation results | Test pass/fail table, lint/type error display | 1d | 7.3 |
| Patch actions | Apply, reject, download buttons | 0.5d | Diff viewer |

---

## Epic 9: Enterprise Features (V2)

| Task | Subtasks | Effort |
|---|---|---|
| CI/CD integration | GitHub Actions plugin, GitLab CI template | 2d |
| Webhook system | Event-driven webhooks, secret signing | 1.5d |
| Trend analysis | Aggregated stats, recurring bug patterns | 2d |
| Team management | Organizations, roles, invites | 2d |
| Audit log UI | Searchable event history | 1d |

---

## Epic 10: SaaS Platform (V3)

| Task | Subtasks | Effort |
|---|---|---|
| Multi-tenant isolation | Schema-per-tenant or row-level security | 3d |
| Billing integration | Stripe subscriptions, metered usage | 2d |
| SSO support | OAuth (Google, GitHub), SAML, LDAP | 3d |
| AI provider abstraction | OpenAI, Anthropic, Gemini plugins | 2d |
| MicroVM isolation | gVisor/Kata integration | 3d |
| SLA management | Priority queues, dedicated workers | 2d |
