# CodeCoroner — AI-Assisted Debugging & Root Cause Analysis Platform

![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/django-5.2-green)
![React](https://img.shields.io/badge/react-18-61DAFB)
![Tests](https://img.shields.io/badge/tests-75%20passed-green)
![License](https://img.shields.io/badge/license-AGPLv3-blue)

## What is CodeCoroner?

CodeCoroner is an AI-native debugging platform that automates root cause analysis (RCA) and fix suggestion. Given a Git repository, logs, stacktraces, and error descriptions, it:

1. **Indexes** the repository (AST parsing, semantic chunking)
2. **Generates embeddings** and stores them in a vector database (pgvector)
3. **Analyzes** the error context (logs, stacktraces, descriptions)
4. **Localizes** the bug (ranks suspicious files by probability)
5. **Performs Root Cause Analysis** via LLM reasoning
6. **Generates** a comprehensive report
7. **Suggests** a fix with unified diff, AI-ready implementation plan, and detailed explanation

Unlike a simple RAG chatbot, CodeCoroner runs a **multi-agent pipeline** with specialized AI agents (Repository Indexer, Log Analyzer, Bug Localizer, Root Cause Agent, Patch Generator, Report Generator). Progress is streamed to the UI in **real time over WebSocket**, generation is **deterministic** (temperature 0 + robust JSON recovery), and each AI stage can be **toggled on/off from the Admin panel** (e.g. disable Fix Suggestion when only localization is needed).

### AI Pipeline (per analysis run)

| Step | Key | Purpose |
|---|---|---|
| 1. Repository indexing | `ensure_repo_indexed` | Clone/pull, tree-sitter chunking, batch embeddings into pgvector |
| 2. Log Analysis | `analyze_input` | Parse stacktraces/logs from the error context |
| 3. Bug Localization | `bug_localization` | Hybrid retrieval + LLM ranking of suspicious files |
| 4. Root Cause Analysis | `root_cause` | LLM reasoning with cause chain and confidence score |
| 5. Fix Suggestion | `fix_suggestion` | Unified diff + implementation plan (never touches test files) |
| 6. Report Generation | `generate_report` | Multi-section markdown report |

Every stage can be **disabled from Admin → AI Pipeline**; disabled stages are skipped and reported as `skipped` in the UI, and later stages degrade gracefully (the report states which steps were not run instead of inventing content).

## Architecture Overview

```
                    ┌─────────────┐
                    │  React SPA  │  Frontend (Port 3000)
                    └──────┬──────┘
                           │ HTTP / WebSocket
                    ┌──────▼──────┐
                    │  Nginx      │  Reverse Proxy (Port 8080)
                    └──────┬──────┘
               ┌───────────┼───────────┐
               ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Django   │ │  Daphne   │ │  Frontend│
        │  REST API │ │ WebSocket │ │  Static  │
        └─────┬────┘ └──────────┘ └──────────┘
              │
        ┌─────▼──────────┐
        │  Celery Worker  │  Async task queue
        └─────┬──────────┘
              │
    ┌─────────┼─────────────┐
    ▼         ▼             ▼
┌────────┐ ┌────────┐ ┌──────────┐
│Postgres│ │ Redis  │ │ Ollama   │
│+pgvector│ │        │ │ LLM +    │
│        │ │        │ │ Embeddings│
└────────┘ └────────┘ └──────────┘
```

### Containers (11 services)

| Service | Image | Purpose |
|---|---|---|
| `postgres` | pgvector/pgvector:pg16 | Database + vector storage |
| `redis` | redis:7-alpine | Cache, Celery broker, WebSocket |
| `minio` | minio/minio | S3-compatible artifact storage |
| `ollama` | ollama/ollama | Local LLM (Qwen2.5-Coder, Nomic-Embed) |
| `django` | custom | REST API, admin, ORM |
| `daphne` | custom | ASGI WebSocket server |
| `celery` | custom | Async task execution |
| `beat` | custom | Celery beat scheduler |
| `frontend` | custom | React SPA (Nginx) |
| `ai-engine` | custom | Agent server (Ollama client) |
| `nginx` | nginx:alpine | Reverse proxy, static files |

## Tech Stack

### Backend
- **Python 3.13** + **Django 5.2** + **DRF 3.18**
- **Celery 5.4** + **Redis** (task queue)
- **Channels** (WebSocket for real-time status)
- **PostgreSQL 16** + **pgvector** (vector search)
- **Tree-sitter** (multi-language AST parsing)
- **GitPython** (repository management)

### Frontend
- **React 18** + **TypeScript 5**
- **Vite 5** (build tool)
- **Tailwind CSS 3** + **shadcn/ui** (UI)
- **TanStack Query** (server state)
- **Zustand** (client state)
- **React Router v6** (routing)

### AI
- **Ollama** (local LLM execution)
- **nomic-embed-text** (768-dim code embeddings)
- **qwen2.5-coder:3b** (default tier — analysis pipeline; auto-downloaded on startup)
- **qwen2.5-coder:3b / 7b / 14b** (fast / balanced / precise tiers, selectable in Admin Settings)
- **Deterministic generation**: `temperature=0` everywhere, strict JSON prompts, tolerant JSON parsing (unterminated strings recovered)

### Infrastructure
- **Podman** (daemonless container runtime)
- **Podman Compose** (orchestration)
- **Nginx** (reverse proxy)
- **MinIO** (S3-compatible blob storage)

## Project Structure

```
codecoroner/
├── backend/                    # Django backend
│   ├── config/                 # Settings (base/dev/prod/test), Celery, ASGI
│   ├── accounts/               # User model, JWT auth, API tokens
│   ├── projects/               # Project CRUD, memberships, RBAC
│   ├── repositories/           # Git service, indexing, chunking, embeddings
│   ├── analyses/               # Pipeline orchestrator, bug localization, RCA
│   ├── reports/                # Report generation (Jinja2 → Markdown)
│   └── webhooks/               # Event-driven webhook dispatcher
│
├── frontend/                   # React SPA
│   └── src/
│       ├── api/                # Axios client, auth, CRUD APIs
│       ├── components/         # UI components (shadcn-style)
│       ├── hooks/              # React Query hooks, auth
│       ├── pages/              # Route pages
│       ├── stores/             # Zustand stores
│       └── types/              # TypeScript domain types
│
├── ai-engine/                  # AI agents (separate service)
│   ├── agents/                 # 9 specialized agents
│   │   ├── repository_indexer/ # AST parsing, semantic chunking
│   │   ├── embedding_generator/# Vector embedding generation
│   │   ├── retrieval_engine/   # Hybrid search (vector + FTS)
│   │   ├── log_analyzer/       # Stacktrace/log parsing
│   │   ├── bug_localizer/      # Suspicion scoring
│   │   ├── root_cause/         # LLM-driven RCA
│   │   ├── patch_generator/    # Git diff generation (V1)
│   │   ├── validation_agent/   # Test/static analysis execution (V1)
│   │   └── report_generator/   # Final report compilation
│   └── core/                   # Ollama client, config
│
├── sandbox/                    # Isolated code execution container
├── infra/                      # Nginx, Postgres init, monitoring
├── podman-compose.yml          # 10-service orchestration
└── Makefile                    # Convenience commands
```

## Running on Windows (WSL 2 Required)

Windows non ha Podman nativamente. La via più semplice è usare **WSL 2 (Windows Subsystem for Linux)** con una distribuzione Ubuntu o Fedora.

### Step 1: Install WSL 2

Apri **PowerShell come Amministratore** ed esegui:

```powershell
# Installa WSL 2 con Ubuntu
wsl --install -d Ubuntu-24.04

# Riavvia il computer se richiesto
# Poi imposta WSL 2 come default
wsl --set-default-version 2
```

Dopo il riavvio, avvia Ubuntu:

```powershell
wsl ~ -d Ubuntu-24.04
```

Completa la creazione dell'utente Linux quando richiesto.

### Step 2: Install Podman & Podman Compose (dentro WSL)

```bash
# Aggiorna i pacchetti
sudo apt update && sudo apt upgrade -y

# Installa Podman
sudo apt install -y podman podman-compose rsync

# Verifica
podman --version
podman-compose --version
```

### Step 3: Clona o copia il progetto

```bash
# Se usi Git:
git clone <repo-url> ~/codecoroner

# Oppure copia da Windows a WSL (usa rsync, cp è lento a causa di node_modules)
rsync -av --exclude node_modules \
  /mnt/c/Users/Utente/.../CodeCoroner/ \
  ~/codecoroner/

cd ~/codecoroner
```

> **Nota**: `cp -r` da `/mnt/c/` è lentissimo se `frontend/node_modules` è presente. Usa sempre `rsync --exclude node_modules`.

### Step 4: Configura l'ambiente

```bash
# Crea il .env
cp .env.example .env

# Genera package-lock.json (necessario per npm ci nel Dockerfile)
cd frontend && npm install && cd ..
```

### Step 5: Avvia tutto con Podman Compose

```bash
# Build e avvia tutti i servizi
podman-compose up -d --build

# Controlla che tutto sia partito
podman-compose ps

# Vedi i log
podman-compose logs -f
```

> **Se qualche container resta in `Exited`**: potrebbe usare un'immagine vecchia. Rimuovi i container bloccanti e riprova:
> ```bash
> podman-compose down
> podman rm <container_id> # rimuovi quelli con nomi duplicati
> podman-compose up -d
> ```

### Step 6: Crea superuser e (opzionale) scarica modelli Ollama

```bash
# Crea superuser admin
podman-compose exec django python manage.py createsuperuser

# (Opzionale) Scarica i modelli Ollama
podman-compose exec ollama ollama pull nomic-embed-text
```

### Step 7: Apri nel browser

- **Frontend**: http://localhost:8080
- **API Django**: http://localhost:8000/api/v1/
- **Admin Django**: http://localhost:8000/admin/
- **MinIO Console**: http://localhost:9001
- **Ollama API**: http://localhost:11434/api/tags

### Comandi utili (Makefile)

```bash
make up       # Avvia tutti i servizi
make down     # Ferma tutti i servizi
make build    # Ricostruisce le immagini (fatelo dopo modifiche ai Dockerfile/requirements!)
make logs     # Vedi i log in tempo reale
make migrate  # Esegue le migrazioni DB
make test     # Esegue i test backend (pytest in container)
make lint     # Ruff check + mypy in container
make shell    # Apre Django shell
make seed     # Popola il DB con dati base (admin@codecoroner.dev / adminadmin) — eseguito anche automaticamente al primo avvio
make seed-demo # Popola il DB con dati demo/test (bob, alice, progetto Flask Demo)
make superuser # Crea superuser
make ps       # Stato dei container
make restart  # down + up
make clean    # Ferma tutto e pulisce i volumi (cancella TUTTE le immagini in cache!)
```

## Troubleshooting

### `npm ci` fallisce: package-lock.json mancante

Se `npm ci` fallisce nel build del frontend, manca `package-lock.json`. Generalo:

```bash
cd frontend && npm install && cd ..
```

Poi ricopia il progetto in WSL.

### `ImportError: Couldn't import Django` / Moduli non trovati

Verifica che l'immagine django sia stata ricostruita con l'ultima versione del Dockerfile:

```bash
podman-compose build --no-cache django
podman-compose up -d django
```

### `relation "..." does not exist` / Migrazioni fallite

Le migrazioni NON vengono più eseguite automaticamente all'avvio. Dopo un reset del database o un pull con nuove migrazioni, applicale esplicitamente:

```bash
make migrate
# e se serve ricreare i dati base:
make seed
```

### Container "name already in use"

Container vecchi con lo stesso nome bloccano quelli nuovi. Rimuovili:

```bash
podman-compose down
podman rm <container_id>
podman-compose up -d
```

### Porte già in uso

Alcune porte (5432, 6379, 8000, etc.) potrebbero essere occupate da altri servizi. Controlla:

```bash
sudo ss -tlnp | grep -E '5432|6379|9000|11434|8000|8080|3000'
```

### Immagini grandi / pull di Ollama (3 GB)

`ollama/ollama:latest` pesa ~3 GB e viene scaricato solo al primo build. Evita `podman system prune -a` che cancella tutte le immagini in cache, incluse quelle già scaricate.

## Alternative a WSL (sconsigliate)

| Metodo | Pro | Contro |
|---|---|---|
| **WSL 2 + Podman** | Performante, supporto completo | Richiede configurazione iniziale |
| **Docker Desktop** | UI grafica, familiare | Non Podman, licenza商用 per team > 250 |
| **Virtual Machine** | Isolamento completo | Overhead, più complesso |
| **Native Windows Podman** | Podman 5+ supporta Windows | Sperimentale, instabile |

**Raccomandazione**: WSL 2 con Ubuntu 24.04 è la via più stabile e performante.

## API Reference

### Authentication
```
POST /api/v1/auth/register/     # Register new user
POST /api/v1/auth/login/        # Login (returns JWT)
GET  /api/v1/auth/me/           # Current user info
```

### Projects
```
GET    /api/v1/projects/        # List projects
POST   /api/v1/projects/        # Create project
GET    /api/v1/projects/{id}/   # Project detail
PUT    /api/v1/projects/{id}/   # Update project
DELETE /api/v1/projects/{id}/   # Delete project
```

### Repositories
```
GET    /api/v1/repositories/            # List repos
POST   /api/v1/repositories/            # Add repo (git_url, branch, project)
GET    /api/v1/repositories/{id}/       # Repo detail
POST   /api/v1/repositories/{id}/index/ # Trigger indexing
GET    /api/v1/repositories/{id}/files/ # List indexed files
GET    /api/v1/repositories/{id}/chunks/# List code chunks
```

### Analyses
```
POST   /api/v1/analyses/                         # Submit analysis
GET    /api/v1/analyses/                         # List analyses
GET    /api/v1/analyses/{id}/                    # Analysis detail
GET    /api/v1/analyses/{id}/status/             # Poll status
GET    /api/v1/analyses/{id}/localization/       # Bug localization results
GET    /api/v1/analyses/{id}/root-cause/         # Root cause analysis
GET    /api/v1/analyses/{id}/fix-suggestion/     # Fix suggestion (diff + plan + explanation)
GET    /api/v1/analyses/{id}/report/             # Final report
```

### Webhooks
```
GET/POST /api/v1/webhooks/                       # List / create webhook
GET/PUT/DELETE /api/v1/webhooks/{id}/            # Webhook detail / update / delete
POST   /api/v1/webhooks/{id}/test/               # Fire a test event
```

### Dashboard & Admin
```
GET  /api/v1/dashboard/summary/                  # Metrics (analyses, repos, active runs)
GET  /api/v1/dashboard/activity/                 # Recent activity feed
GET/PATCH /api/v1/auth/admin/model-settings/     # AI model tier + AI pipeline step toggles
```

WebSocket: `ws://localhost:8080/ws/analyses/{id}/` (real-time status; stage completed/failed/skipped events)

## Development Status

### ✅ Completed
- **Foundation** — Django, DRF, Celery, PostgreSQL, auth, Podman Compose
- **Repository Indexing** — Tree-sitter, chunking (Python, JavaScript, Go, Rust, Java, C/C++), auto-pull
- **Embeddings** — Ollama, pgvector, batch processing
- **Bug Localization** — Log analyzer, hybrid search (vector + FTS), suspicion scoring
- **Root Cause Analysis** — LLM-driven RCA with confidence scoring
- **Fix Suggestion** — Unified diff + AI-ready fix plan + explanation; never touches test files
- **Report Generation** — Multi-section markdown report, robust to disabled/missing stages
- **Frontend** — Full SPA: projects, repos, analyses list/detail/create, dashboard, admin settings
- **Real-time** — WebSocket + Channels + Daphne, stage-level notifications in the UI
- **Deterministic AI** — temperature 0, strict JSON + tolerant parsing, model tiers in Admin
- **Admin controls** — AI model tier selector + per-stage pipeline toggles
- **Webhooks** — CRUD + test events, dispatched on analysis lifecycle
- **Access control** — project memberships, groups, repo visibility for groups/superusers
- **Auth options** — JWT (rotating refresh tokens, blacklist) + optional LDAP group mapping
- **Backend test suite** — 75 passing (projects CRUD, repos, analyses, webhooks)

### 🔜 Next
- **CI/CD** — GitHub Actions (pytest + ruff + mypy + tsc/build in clean containers)
- **Sandbox validation** — Wire the validation container into the pipeline (currently a stub)
- **Frontend tests** — Vitest is installed but not configured (`npm run test` missing)
- **TLS/HTTPS** — Certificate termination on nginx + HSTS/CSP headers
- **Deploy & DR runbook** — Backup/restore, staging env

## Production Readiness

The codebase runs the full stack locally on Podman, but several **production gaps remain** before a public deployment. High-priority items:

- **TLS**: nginx serves plaintext on :8080; no certificates, HSTS or CSP at the proxy.
- **Secrets**: `base.py` falls back to a hardcoded dev secret and DB password; webhook secrets are stored in plaintext in the DB.
- **Migrations**: applied explicitly via `make migrate` (no `makemigrations`/`migrate`/`seed_base` at container start anymore); the container starts `runserver` directly.
- **CI/CD**: no pipeline; build reproducibility is only manual (`make build`). Note that `podman-compose up -d` can silently reuse **stale images** — rebuild with `make build` after Dockerfile/requirements changes.
- **Backup & DR**: no pg_dump/minio/media backup scripts, no restore runbook.
- **Observability**: console logging only; no Sentry, Prometheus or Celery failure alerting.
- **Queue hardening**: no `acks_late`/dead-letter queue; Celery beat runs with no scheduled tasks.
- **Data lifecycle**: no git GC, no cleanup for orphaned repos/embeddings, no pgvector index on embeddings (fine at current scale).
- **Input limits**: ai-engine has no size limits on logs/stacktraces (prompt-injection surface).

See `specs/*.md` for design intent — some files have drifted from the current code (trust the code).

## License

Copyright (C) 2026 CodeCoroner.

This project is licensed under the **GNU Affero General Public License v3 (AGPL-3.0)** — see the [LICENSE](LICENSE) file for details.

## Contributing

This is a **solo project** and external contributions via pull requests are **not accepted** at this time. The repository is not open for public collaboration — no forks, no PRs, no external code submissions.

If you find a bug or have a suggestion, please open a GitHub issue. All code is pushed exclusively by the project maintainer.

---

Built with Python, Django, React, Podman, and Ollama.
