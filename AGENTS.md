# AGENTS.md

CodeCoroner: AI debugging/RCA platform. Monorepo with 4 codebases:
- `backend/` — Django 5.1 + DRF + Celery + Channels (Python 3.13)
- `frontend/` — React 18 + Vite + TypeScript
- `ai-engine/` — FastAPI agent server (port 8002) that calls Ollama
- `infra/`, `sandbox/`, `specs/`, `scripts/` — nginx/postgres config, validation container stub, design docs, helper scripts

## Dev environment

- The stack only runs via **Podman Compose, which requires WSL2 on Windows**. Native Windows won't work. All backend/frontend processes run in containers.
- Dockerfiles use bind mounts (`./backend:/app`, `./ai-engine:/app`, `./frontend:/app`), so Python/TS edits hot-reload. The **django container runs `makemigrations` + `migrate` on every startup** (podman-compose.yml) and migrations are committed.
- `make` targets are the canonical commands (`make up/down/build/logs/migrate/test/lint/shell/seed/superuser/ps`). `make clean` prunes ALL cached images including the ~3GB Ollama image — avoid unless intended.

## Commands

```bash
podman-compose up -d --build   # full stack
make test                      # pytest inside django container
make lint                      # ruff check + mypy inside django container
podman-compose exec django pytest <path>::<test>   # single test
make seed                      # demo data (admin@codecoroner.dev / adminadmin)
```

- Frontend: `npm run lint` (eslint), `npm run typecheck` (`tsc --noEmit`), `npm run build` (`tsc -b && vite build`). Vite dev server runs on 5173 proxying `/api` and `/ws` to `:8000`. **Vitest is installed but no test script is configured** — frontend tests effectively don't run.
- ai-engine runs `uvicorn agents.agent_server:app` on 8002; no pytest config of its own, but `ai-engine/tests/` exists.

## Architecture notes

- Analysis pipeline is a synchronous state machine: `backend/analyses/orchestrator.py` runs inside a Celery task (`analyses/tasks.py`) and calls the ai-engine over plain HTTP via httpx (300s timeouts) at `AI_ENGINE_URL` (default `http://ai-engine:8002`). Endpoints: `/embed`, `/index`, `/analyze-logs`, `/localize-bug`, `/analyze-root-cause`, `/suggest-fix`, `/generate-report`, `/health`.
- Indexing flow: `repositories/tasks.py` — clone/pull → tree-sitter chunking (`chunking.py`, `IGNORED_DIRS`/`IGNORED_EXTENSIONS` sets) → batch embed via ai-engine `/embed` (nomic-embed-text, 768-dim) → store in pgvector `ChunkEmbedding`.
- Repos are cloned into `backend/media/repos/` (gitignored; `repo_cache` volume shared read-only with ai-engine). `backend/media/` and `backend/static/` are gitignored build/runtime dirs.
- Settings split under `backend/config/settings/`: `dev` (used by compose, debug toolbar, no throttling), `prod` (Dockerfile default), `test` (used by pytest, `CELERY_TASK_ALWAYS_EAGER=True`, locmem cache). mypy is wired to `config.settings.dev` via pyproject.
- **`specs/*.md` are design docs that have drifted from the code** (e.g., they describe `analyses/tasks/` dirs and a gRPC agent server; actual code is `analyses/tasks.py` and plain HTTP). Use them for intent, but trust the code.

## Testing

- Real tests live in `backend/*/tests/` (pytest-django) and `ai-engine/tests/`. **Ignore the root-level `test_*.py` / `test_*.sh` files — they are untracked ad-hoc smoke scripts with hardcoded JWTs** that hit a running server; not part of the suite.
- Backend tests need PostgreSQL with the `vector` extension (test DB `codecoroner_test`). Custom `common/test_runner.PgVectorTestRunner` creates the test DB + extension; `infra/postgres/init.sql` sets up extensions for the dev DB. Tests can't run against SQLite.

## Style & tooling

- Python: ruff, **single-quote style enforced by `ruff-format`** (`quote-style = "single"`), line-length 100. pre-commit runs ruff `--fix`, ruff-format, and mypy with django-stubs. Run `make lint` to verify.
- AGPL-3.0 licensed, solo project — no external PRs expected.
