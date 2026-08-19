# CodeCoroner — Folder Structure

## Root

```
codecoroner/
├── backend/                  # Django backend
├── frontend/                 # React SPA
├── ai-engine/                # FastAPI agent server (plain HTTP, port 8002)
├── sandbox/                  # Sandbox container stub (not yet wired)
├── infra/                    # Infrastructure (nginx, postgres config)
├── specs/                    # Specification documents (some drifted)
├── scripts/                  # Development scripts (backup, restore, bootstrap)
├── podman-compose.yml        # Podman Compose (MVP)
├── Makefile                  # Common commands
├── .env.example              # Environment template
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
└── AGENTS.md                 # Agent instructions
```

> **Note**: This document reflects the current structure as of 2026-08-18. Some specs/*.md files have drifted from the code — use for intent, trust the code.

## Backend (`backend/`)

```
backend/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py           # Shared settings
│   │   ├── dev.py            # Development
│   │   ├── prod.py           # Production
│   │   └── test.py           # Testing
│   ├── urls.py               # Root URL config
│   ├── wsgi.py
│   ├── asgi.py               # WebSocket/ASGI
│   ├── celery.py             # Celery app
│   └── celerybeat.py         # Scheduled tasks
│
├── accounts/
│   ├── __init__.py
│   ├── models.py             # User, ApiToken
│   ├── serializers.py        # RegisterSerializer, UserSerializer
│   ├── views.py              # RegisterView, LoginView, UserDetailView
│   ├── urls.py               # /api/v1/auth/
│   ├── permissions.py        # IsOwner, IsAdmin
│   ├── authentication.py     # JWT config
│   ├── admin.py
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_auth.py
│
├── projects/
│   ├── __init__.py
│   ├── models.py             # Project, ProjectMembership
│   ├── serializers.py
│   ├── views.py              # ProjectViewSet
│   ├── urls.py               # /api/v1/projects/
│   ├── permissions.py        # ProjectPermission
│   ├── services.py           # ProjectService
│   ├── admin.py
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_services.py
│
├── repositories/
│   ├── __init__.py
│   ├── models.py             # Repository, IndexedFile, CodeChunk, ChunkEmbedding
│   ├── serializers.py
│   ├── views.py              # RepositoryViewSet
│   ├── urls.py               # /api/v1/repositories/
│   ├── services.py           # GitService, RepositoryService
│   ├── chunking.py           # SemanticChunker (tree-sitter)
│   ├── tasks.py              # Celery tasks (clone, index, embeddings, daily_pulls)
│   ├── admin.py
│   └── tests/
│       ├── test_models.py
│       ├── test_services.py
│       ├── test_chunking.py
│       └── test_views.py
│
├── analyses/
│   ├── __init__.py
│   ├── models.py             # Analysis, AnalysisRun, BugLocalization
│   │                         # SuspiciousFileScore, RootCause, Patch
│   │                         # PatchValidation, Report
│   ├── serializers.py
│   ├── views.py              # AnalysisViewSet
│   ├── urls.py               # /api/v1/analyses/
│   ├── orchestrator.py       # AnalysisOrchestrator (state machine)
│   ├── tasks.py              # Celery task: run_analysis_pipeline
│   ├── consumers.py          # WebSocket consumer for status
│   ├── routing.py            # WebSocket routing
│   └── tests/
│       ├── test_models.py
│       ├── test_orchestrator.py
│       ├── test_views.py
│       ├── test_pipeline.py
│       └── test_tenant_isolation.py
│
├── reports/
│   ├── __init__.py
│   ├── serializers.py
│   ├── services.py           # ReportService (Jinja2 rendering)
│   ├── generators.py         # ReportGenerator (markdown templates)
│   └── templates/
│       └── report.md.j2      # Jinja2 report template
│
├── webhooks/
│   ├── __init__.py
│   ├── models.py             # Webhook
│   ├── crypto.py             # Fernet encryption
│   ├── services.py           # WebhookService (dispatch events)
│   └── tasks.py              # dispatch_webhook_task
│
├── common/
│   ├── __init__.py
│   ├── models.py             # BaseModel (UUID, timestamps)
│   ├── pagination.py         # Custom pagination
│   ├── exceptions.py         # Custom exception handling
│   ├── logging.py            # JSON formatter, handlers
│   ├── cleanup.py            # Purge stale data (git GC, orphan dirs, retention)
│   ├── tasks.py              # Celery tasks (purge, dlq_receiver)
│   ├── celery.py             # DLQTask base class
│   ├── management/
│   │   └── commands/
│   │       └── dlq.py        # DLQ management command
│   └── tests/
│       └── test_logging.py
│
├── static/                   # Collected static files
├── media/                    # User uploads + repo cache (gitignored)
├── templates/                # Django templates (admin, base)
│
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml            # Project metadata, ruff, mypy config
├── Dockerfile
└── .dockerignore
```

## Frontend (`frontend/`)

```
frontend/
├── public/
│   ├── favicon.ico
│   └── og-image.png
│
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # App shell + router
│   ├── index.css             # Tailwind imports + globals
│   │
│   ├── api/
│   │   ├── client.ts         # Axios instance with interceptors
│   │   ├── auth.ts           # Auth API calls
│   │   ├── projects.ts       # Project API calls
│   │   ├── repositories.ts   # Repository API calls
│   │   ├── analyses.ts       # Analysis API calls
│   │   └── reports.ts        # Report API calls
│   │
│   ├── hooks/
│   │   ├── useAuth.ts        # Auth context/state
│   │   ├── useProjects.ts    # TanStack Query hooks
│   │   ├── useRepositories.ts
│   │   ├── useAnalyses.ts
│   │   ├── useWebSocket.ts   # WebSocket connection
│   │   └── useLocalization.ts
│   │
│   ├── stores/
│   │   ├── authStore.ts      # Zustand auth store
│   │   └── analysisStore.ts  # Zustand analysis store
│   │
│   ├── types/
│   │   ├── api.ts            # API response types
│   │   ├── models.ts         # Domain model types
│   │   └── ui.ts             # UI-specific types
│   │
│   ├── components/
│   │   ├── ui/               # shadcn/ui primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Dialog.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Progress.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   └── Toast.tsx
│   │   │
│   │   ├── layout/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   ├── Breadcrumbs.tsx
│   │   │   └── UserMenu.tsx
│   │   │
│   │   ├── projects/
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── ProjectForm.tsx
│   │   │   ├── ProjectFilters.tsx
│   │   │   └── MemberList.tsx
│   │   │
│   │   ├── repositories/
│   │   │   ├── AddRepoForm.tsx
│   │   │   ├── RepoTable.tsx
│   │   │   ├── RepoStatusBadge.tsx
│   │   │   └── FileList.tsx
│   │   │
│   │   ├── analyses/
│   │   │   ├── AnalysisForm.tsx
│   │   │   ├── AnalysisTable.tsx
│   │   │   ├── StatusTimeline.tsx
│   │   │   ├── StepIndicator.tsx
│   │   │   └── AnalysisFilters.tsx
│   │   │
│   │   ├── localization/
│   │   │   ├── SuspicionChart.tsx
│   │   │   ├── SuspiciousFileRow.tsx
│   │   │   └── CodeViewer.tsx
│   │   │
│   │   ├── rca/
│   │   │   ├── CauseChainFlow.tsx
│   │   │   ├── RCASummary.tsx
│   │   │   └── EvidenceLinks.tsx
│   │   │
│   │   ├── patch/
│   │   │   ├── DiffViewer.tsx
│   │   │   ├── ValidationResults.tsx
│   │   │   └── PatchActions.tsx
│   │   │
│   │   ├── report/
│   │   │   ├── ReportMarkdown.tsx
│   │   │   └── ExportOptions.tsx
│   │   │
│   │   └── common/
│   │       ├── StatsCard.tsx
│   │       ├── EmptyState.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── LoadingSpinner.tsx
│   │       ├── ConfirmDialog.tsx
│   │       └── ActivityChart.tsx
│   │
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ProjectListPage.tsx
│   │   ├── ProjectCreatePage.tsx
│   │   ├── ProjectDetailPage.tsx
│   │   ├── AnalysisListPage.tsx
│   │   ├── AnalysisDetailPage.tsx
│   │   ├── BugLocalizationPage.tsx
│   │   ├── RootCausePage.tsx
│   │   ├── PatchPage.tsx
│   │   ├── ReportPage.tsx
│   │   └── UserSettingsPage.tsx
│   │
│   └── lib/
│       ├── utils.ts          # cn(), formatters
│       └── constants.ts      # Routes, API URLs
│
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── tailwind.config.ts
├── postcss.config.js
├── package.json
├── nginx.conf               # Frontend nginx config
└── Dockerfile
```

## AI Engine (`ai-engine/`)

```
ai-engine/
├── agents/
│   ├── __init__.py
│   ├── agent_server.py       # FastAPI server (plain HTTP, port 8002)
│   │
│   ├── log_analyzer.py       # Analyze logs/stacktrace → structured queries
│   ├── bug_localizer.py      # Hybrid search + scoring
│   ├── root_cause.py         # RCA chain generation
│   ├── patch_generator.py    # Diff + fix plan + explanation
│   ├── report_generator.py   # Markdown report assembly
│   └── validation_agent.py   # Stub (not wired in pipeline)
│
├── core/
│   ├── __init__.py
│   ├── ollama_client.py      # Ollama async HTTP client
│   ├── models.py             # Pydantic models for requests/responses
│   └── config.py             # Settings (Pydantic)
│
├── tests/
│   ├── test_log_analyzer.py
│   ├── test_bug_localizer.py
│   ├── test_root_cause.py
│   ├── test_patch_generator.py
│   └── test_report_generator.py
│
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└ .dockerignore
```

> **Note**: No gRPC — the Django backend calls ai-engine via plain HTTP (httpx) at `AI_ENGINE_URL` (default `http://ai-engine:8002`). Endpoints: `/embed`, `/index`, `/analyze-logs`, `/localize-bug`, `/analyze-root-cause`, `/suggest-fix`, `/generate-report`, `/health`.

## Sandbox (`sandbox/`)

```
sandbox/
├── Dockerfile                # Sandbox runtime image (stub)
├── scripts/
│   └── validate.sh           # Placeholder
└── podman-compose.yml        # Dynamic compose template (unused)
```

> **Note**: The sandbox validation container exists as a stub but is **not wired into the pipeline**. The Validation Agent in ai-engine returns `not_implemented`. Deferred to future work.

## Infrastructure (`infra/`)

```
infra/
├── nginx/
│   ├── nginx.conf            # Reverse proxy + TLS termination (:8443)
│   └── entrypoint.sh         # Self-signed cert generation, HSTS opt-in
├── postgres/
│   └── init.sql              # Extensions (pgvector, pg_trgm) + init
└── scripts/
    ├── backup.sh             # pg_dump + repo volume backup
    └── restore.sh            # Restore from backup
```

> **Note**: No monitoring stack (Prometheus/Grafana) — observability is JSON logs only. TLS self-signed cert auto-generated on first nginx start into `nginx_certs` volume; HSTS opt-in via `ENABLE_HSTS=true`.

## Root files

```
.gitignore
.env.example
Makefile
README.md
AGENTS.md                       # Instructions for AI coding agents
podman-compose.yml              # MVP compose
.python-version                 # 3.13
```
