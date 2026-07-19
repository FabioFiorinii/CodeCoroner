# CodeCoroner — MVP Roadmap

## Release Phases

```
MVP (3 months)              V1 (2 months)          V2 (2 months)          V3 (ongoing)
────────────────────────    ────────────────        ────────────────        ────────────────
Core pipeline               Patch Generation        Enterprise Features     SaaS Platform
Bug Localization + RCA      Validation Pipeline     Multi-project          Multi-tenant
Basic UI                    Static Analysis         Collaboration          SSO/RBAC
Single-language (Python)    Test Execution          CI/CD Integration      Audit Logging
Ollama only                 Multi-language          Trend Analysis         Custom Models
Podman Compose              Patch Report            Team Management        API Marketplace
│                           │                       │                       │
└───────────────────────────┴───────────────────────┴───────────────────────┘
   Month 1-3                   Month 4-5               Month 6-7               Month 8+
```

## MVP — Months 1-3 (Bug Localization + RCA)

### Week 1-2: Foundation

- [x] Project setup: Django, DRF, Celery, PostgreSQL, Redis
- [x] Podman Compose configuration
- [x] User authentication (register, login, JWT)
- [x] Project CRUD API + model
- [x] Repository model + Git clone service

### Week 3-4: Repository Indexing

- [x] Tree-sitter integration (Python first)
- [x] File walking and AST parsing
- [x] Semantic chunking (functions, classes, blocks)
- [x] CodeChunk model + storage
- [x] Repository status tracking

### Week 5-6: Embeddings

- [x] Ollama integration (embedding endpoint)
- [x] EmbeddingGenerator agent
- [x] Chunk → vector pipeline
- [x] pgvector storage + IVFFlat index
- [x] Embedding batch processing via Celery

### Week 7-8: Bug Localization

- [x] Log Analyzer agent
- [x] Hybrid search engine (vector + FTS)
- [x] File scoring algorithm
- [x] SuspiciousFile ranking
- [x] BugLocalization API + model

### Week 9-10: Root Cause Analysis

- [x] Root Cause Agent (Ollama LLM)
- [x] Code context retrieval for top files
- [x] RCA prompt engineering
- [x] Structured RCA output
- [x] RootCause model + API

### Week 11-12: MVP UI & Polish

- [x] React project setup + routing
- [x] Dashboard page (stats cards)
- [x] Project list + create pages
- [x] Repository management UI
- [x] Analysis submission form
- [x] Status timeline (WebSocket)
- [x] Bug localization results view
- [x] Root cause results view
- [x] Report view (MVP simple)
- [x] Pagination, error handling, loading states
- [x] E2E test for core flow
- [x] Documentation

### MVP Deliverables

| Artifact | Description |
|---|---|
| Working pipeline: clone → index → embed → localize → RCA → report | Core flow end-to-end |
| REST API with all CRUD endpoints | Full backend API |
| React dashboard for 5 core pages | Projects, repos, analyses, localization, RCA |
| Podman Compose (8 containers) | One command to start |
| Seed script with demo data | Quick demo setup |
| Test suite >70% coverage | Backend tests |
| User documentation | README + API docs |

---

## V1 — Months 4-5 (Patch Generation)

### Month 4

- [x] Patch Generator agent
- [x] Sandbox container (Podman)
- [x] Patch application in sandbox
- [x] Test execution (pytest) in sandbox
- [x] Static analysis (ruff, mypy) in sandbox
- [x] Validation scoring algorithm

### Month 5

- [x] Multi-language support (TypeScript, Go, Rust, Java)
- [x] Patch UI (diff viewer)
- [x] Validation results UI
- [x] Patch report section
- [x] Cross-encoder reranking (V1)
- [x] Webhook notifications
- [x] Performance optimization (caching, query tuning)

---

## V2 — Months 6-7 (Enterprise Readiness)

### Month 6

- [x] CI/CD integration (GitHub Actions, GitLab CI plugins)
- [x] Multi-project dashboard
- [x] Collaboration features (comments, sharing)
- [x] Analysis history with trends
- [x] Scheduled/recurring analyses

### Month 7

- [x] Team management (orgs, teams)
- [x] Advanced RBAC
- [x] Audit log UI
- [x] Custom agent pipeline configuration
- [x] HNSW vector index
- [x] OpenTelemetry tracing

---

## V3 — Month 8+ (SaaS Platform)

### Month 8-9

- [x] Multi-tenant architecture
- [x] SSO (OAuth, SAML, LDAP)
- [x] Billing & subscription (Stripe)
- [x] API keys management + marketplace
- [x] OpenAI/Anthropic/Gemini providers
- [x] Model fallback logic

### Month 10+

- [x] MicroVM isolation (gVisor/Kata Containers)
- [x] Dedicated inference endpoints
- [x] SLA tiers (standard, priority, dedicated)
- [x] Custom model fine-tuning
- [x] On-premise deployment Helm chart
- [x] SOC 2 compliance
- [x] Public API documentation portal
