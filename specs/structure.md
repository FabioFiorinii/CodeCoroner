# CodeCoroner — Folder Structure

## Root

```
codecoroner/
├── backend/                  # Django backend
├── frontend/                 # React SPA
├── ai-engine/                # AI agents (standalone service)
├── sandbox/                  # Sandbox container configuration
├── infra/                    # Infrastructure (nginx, scripts)
├── specs/                    # Specification documents
├── docs/                     # User documentation
├── scripts/                  # Development scripts
├── .github/                  # CI/CD workflows
├── podman-compose.yml        # Podman Compose (MVP)
├── podman-compose.prod.yml   # Production overrides
├── Makefile                  # Common commands
├── .env.example              # Environment template
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
└── AGENTS.md                 # Agent instructions
```

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
│   ├── indexing.py           # Indexing pipeline
│   ├── admin.py
│   └── tests/
│       ├── test_models.py
│       ├── test_services.py
│       ├── test_chunking.py
│       └── test_indexing.py
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
│   ├── services.py           # AnalysisService
│   ├── admin.py
│   ├── consumers.py          # WebSocket consumer for status
│   ├── routing.py            # WebSocket routing
│   └── tests/
│       ├── test_models.py
│       ├── test_orchestrator.py
│       ├── test_views.py
│       └── test_pipeline.py
│
├── analyses/tasks/
│   ├── __init__.py
│   ├── index_tasks.py        # index_repository_task, generate_embeddings_task
│   ├── analysis_tasks.py     # run_analysis_pipeline, bug_localization_task
│   ├── patch_tasks.py        # generate_patch_task, validate_patch_task
│   └── report_tasks.py       # generate_report_task
│
├── reports/
│   ├── __init__.py
│   ├── models.py             # Extra report models if needed
│   ├── services.py           # ReportService (Jinja2 rendering)
│   ├── generators.py         # ReportGenerator (markdown templates)
│   └── templates/
│       └── report.md.j2      # Jinja2 report template
│
├── webhooks/
│   ├── __init__.py
│   ├── models.py             # Webhook
│   ├── services.py           # WebhookService (dispatch events)
│   └── tasks.py              # dispatch_webhook_task
│
├── common/
│   ├── __init__.py
│   ├── models.py             # BaseModel (UUID, timestamps)
│   ├── pagination.py         # Custom pagination
│   ├── exceptions.py         # Custom exception handling
│   ├── middleware.py         # Request logging, rate limiting
│   └── utils.py              # Helpers
│
├── static/                   # Collected static files
├── media/                    # User uploads
├── templates/                # Django templates (admin, base)
│
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml            # Project metadata, ruff config
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
│   ├── base_agent.py         # Abstract base agent
│   ├── agent_server.py       # Agent gRPC/HTTP server
│   │
│   ├── repository_indexer/
│   │   ├── __init__.py
│   │   ├── indexer.py        # RepositoryIndexer agent
│   │   ├── chunker.py        # SemanticChunker (tree-sitter)
│   │   └── languages.py      # Language definitions
│   │
│   ├── embedding_generator/
│   │   ├── __init__.py
│   │   ├── generator.py      # EmbeddingGenerator agent
│   │   └── prefixes.py       # Type prefix strategy
│   │
│   ├── retrieval_engine/
│   │   ├── __init__.py
│   │   ├── engine.py         # HybridSearchEngine
│   │   ├── reranker.py       # CrossEncoderReranker
│   │   └── augmenter.py      # QueryAugmenter
│   │
│   ├── log_analyzer/
│   │   ├── __init__.py
│   │   ├── analyzer.py       # LogAnalyzer agent
│   │   ├── stacktrace.py     # Stacktrace parser
│   │   └── patterns.py       # Error patterns
│   │
│   ├── bug_localizer/
│   │   ├── __init__.py
│   │   ├── localizer.py      # BugLocalizer agent
│   │   └── scorer.py         # File scoring algorithms
│   │
│   ├── root_cause/
│   │   ├── __init__.py
│   │   ├── rca_agent.py      # RootCauseAgent
│   │   └── prompts.py        # RCA prompt templates
│   │
│   ├── patch_generator/
│   │   ├── __init__.py
│   │   ├── generator.py      # PatchGenerator agent
│   │   └── prompts.py        # Patch prompt templates
│   │
│   ├── validation_agent/
│   │   ├── __init__.py
│   │   ├── validator.py      # ValidationAgent
│   │   └── sandbox.py        # Podman sandbox controller
│   │
│   └── report_generator/
│       ├── __init__.py
│       ├── generator.py      # ReportGenerator agent
│       └── templates/        # Report templates (.md.j2)
│
├── core/
│   ├── __init__.py
│   ├── ollama_client.py      # Ollama async HTTP client
│   ├── db.py                 # Database session (SQLAlchemy)
│   ├── models.py             # Agent result models (Pydantic)
│   └── config.py             # Agent settings (Pydantic)
│
├── tests/
│   ├── test_indexer.py
│   ├── test_chunker.py
│   ├── test_embeddings.py
│   ├── test_retrieval.py
│   ├── test_log_analyzer.py
│   ├── test_localizer.py
│   ├── test_rca.py
│   └── test_report.py
│
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── .dockerignore
```

## Sandbox (`sandbox/`)

```
sandbox/
├── Dockerfile                # Sandbox runtime image
├── seccomp-default.json      # Seccomp profile
├── scripts/
│   ├── apply_patch.sh        # Apply patch in workspace
│   ├── run_tests.sh          # Run pytest
│   ├── run_lint.sh           # Run ruff
│   └── run_typecheck.sh     # Run mypy
└── podman-compose.yml        # Dynamic compose for sandbox
```

## Infrastructure (`infra/`)

```
infra/
├── nginx/
│   ├── nginx.conf            # Reverse proxy config
│   ├── ssl/
│   │   ├── cert.pem          # SSL certificate
│   │   └── key.pem           # SSL key
│   └── locations/
│       ├── api.conf          # /api/ → django
│       ├── static.conf       # /static/ → django
│       └── frontend.conf     # / → frontend
│
├── postgres/
│   └── init.sql              # Extensions + initial schema
│
├── monitoring/
│   ├── prometheus.yml
│   └── grafana-dashboard.json
│
├── scripts/
│   ├── bootstrap.sh          # First-time setup
│   ├── backup.sh             # Database backup
│   └── restore.sh            # Database restore
│
└── terraform/                # Future: infra as code
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```

## Root files

```
.gitignore
.env.example
Makefile
README.md
AGENTS.md                       # Instructions for AI coding agents
podman-compose.yml              # MVP compose
podman-compose.prod.yml         # Production overrides
.python-version                 # 3.13
.node-version                   # 22
```
