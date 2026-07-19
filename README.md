# CodeCoroner — AI-Assisted Debugging & Root Cause Analysis Platform

[![CI](https://github.com/your-org/codecoroner/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/codecoroner/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/django-5.1-green)
![React](https://img.shields.io/badge/react-18-61DAFB)
![License](https://img.shields.io/badge/license-MIT-yellow)

## What is CodeCoroner?

CodeCoroner is an AI-native debugging platform that automates root cause analysis (RCA) and bug fixing. Given a Git repository, logs, stacktraces, and error descriptions, it:

1. **Indexes** the repository (AST parsing, semantic chunking)
2. **Generates embeddings** and stores them in a vector database (pgvector)
3. **Correlates** logs, stacktraces, and code
4. **Localizes** the bug (ranks suspicious files by probability)
5. **Performs Root Cause Analysis** via LLM reasoning
6. **Generates** a comprehensive report
7. (V1) **Proposes and validates** a candidate patch

Unlike a simple RAG chatbot, CodeCoroner runs a **multi-agent pipeline** with specialized AI agents (Repository Indexer, Log Analyzer, Bug Localizer, Root Cause Agent, Patch Generator, Validation Agent, Report Generator).

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

### Containers (10 services)

| Service | Image | Purpose |
|---|---|---|
| `postgres` | pgvector/pgvector:pg16 | Database + vector storage |
| `redis` | redis:7-alpine | Cache, Celery broker, WebSocket |
| `minio` | minio/minio | S3-compatible artifact storage |
| `ollama` | ollama/ollama | Local LLM (DeepSeek-Coder, Mistral, Nomic-Embed) |
| `django` | custom | REST API, admin, ORM |
| `daphne` | custom | ASGI WebSocket server |
| `celery_worker` | custom | Async task execution |
| `celery_beat` | custom | Scheduled tasks |
| `frontend` | custom | React SPA (Nginx) |
| `ai-engine` | custom | Agent server (Ollama client) |
| `nginx` | nginx:alpine | Reverse proxy, static files |

## Tech Stack

### Backend
- **Python 3.13** + **Django 5.1** + **DRF 3.15**
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
- **deepseek-coder**:6.7b/14b (RCA, patch generation)
- **mistral**:7b (log analysis, report generation)

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
make logs     # Vedi i log in tempo reale
make build    # Ricostruisce le immagini
make migrate  # Esegue le migrazioni DB
make test     # Esegue i test
make shell    # Apre Django shell
make superuser # Crea superuser
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

Le migrazioni vengono generate automaticamente all'avvio (`makemigrations` + `migrate`). Se il database è stato resettato, basta riavviare django:

```bash
podman-compose restart django
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
POST   /api/v1/analyses/                    # Submit analysis
GET    /api/v1/analyses/                    # List analyses
GET    /api/v1/analyses/{id}/               # Analysis detail
GET    /api/v1/analyses/{id}/status/        # Poll status
GET    /api/v1/analyses/{id}/localization/  # Bug localization results
GET    /api/v1/analyses/{id}/root-cause/    # Root cause analysis
GET    /api/v1/analyses/{id}/patch/         # Generated patch (V1)
GET    /api/v1/analyses/{id}/report/        # Final report
```

WebSocket: `ws://localhost:8080/ws/analyses/{id}/` (real-time status)

## Development Plan (MVP — 3 Months)

| Week | Milestone |
|---|---|
| 1-2 | Foundation: Django, DRF, Celery, PostgreSQL, auth, Podman Compose |
| 3-4 | Repository indexing: Tree-sitter, chunking, file model |
| 5-6 | Embeddings: Ollama, pgvector, vector search |
| 7-8 | Bug localization: Log analyzer, hybrid search, scoring |
| 9-10 | Root cause analysis: LLM agent, prompt engineering, RCA model |
| 11-12 | Frontend MVP: Dashboard, project/repo/analysis pages, status timeline |
| V1 | Patch generation, validation sandbox |
| V2 | Enterprise: teams, webhooks, CI/CD integration |
| V3 | SaaS: multi-tenant, SSO, billing, cloud AI providers |

## License

MIT

---

Built with Python, Django, React, Podman, and Ollama.
