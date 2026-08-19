# Backup & Disaster Recovery Runbook

## What gets backed up

| Data | Source | Notes |
|---|---|---|
| PostgreSQL database | `pg_dump` custom format | users, projects, repos metadata, analyses, reports, **pgvector embeddings** |
| Cloned repos | `repo_cache` volume (`backend/media/repos`) | re-clonable but re-indexing costs time/LLM |

Not backed up (regenerable): static files, MinIO (unused by the app), Ollama model images (re-pullable).

## Create a backup

```bash
make backup
# or: scripts/backup.sh
```

Outputs into `./backups/`:
- `codecoroner-<timestamp>.dump` — compressed DB dump
- `repos-<timestamp>.tar.gz` — repo cache volume

Config (env): `BACKUP_DIR` (default `./backups`), `RETENTION_DAYS` (default 7).

**For real DR, copy `./backups/` off this machine** (external disk / another host / rsync target). A backup that lives on the same disk as the data protects you from nothing.

## Restore

```bash
make restore DUMP=backups/codecoroner-<timestamp>.dump
```

The script runs `pg_restore --clean --if-exists`. Then:

```bash
# 1. optionally restore the repo cache volume
podman run --rm -v repo_cache:/data -v $PWD/backups:/backup:ro alpine \
  tar xzf /backup/repos-<timestamp>.tar.gz -C /data

# 2. start the stack and migrate
podman-compose up -d
make migrate
make seed   # only if the base admin user is missing
```

## Testing the restore (do this periodically)

1. `make backup`
2. Reset the database: `podman-compose down && podman volume rm pg_data`
3. `podman-compose up -d postgres && make migrate`
4. `make restore DUMP=backups/codecoroner-<latest>.dump`
5. Verify: log in, open a project/analysis, confirm embeddings still answer (vector search works).
6. If step 5 fails, fix the runbook — a backup that cannot be restored is not a backup.

## Test evidence (2026-08-19, fresh machine)

Performed on a **fresh WSL2 distro** (Ubuntu 24.04, podman 4.9.3, podman-compose 1.0.6) — no prior state, images pulled from scratch.

1. Copy repo + `backups/` into the fresh distro.
2. `podman-compose up -d postgres`, wait healthy, then `bash scripts/restore.sh backups/codecoroner-20260818-120151.dump` → `pg_restore --clean` OK.
3. Verified in restored DB: `accounts_customuser`, `projects_project`, `repositories_repository`, `analyses_analysisrun`, `repositories_codechunk`, `repositories_chunkembedding` all present; vector search (`embedding <-> embedding`) returns rows.
4. Extracted `repos-20260818-120151.tar.gz` into `codecoroner_repo_cache` → repo dir matches repository id (`ededebd1-…/thefuck`).
5. `podman-compose up -d` (full stack) + `python manage.py migrate` — applied drift-only migrations (axes lockout tables, `repositories.0006_chunkembedding_hnsw`).
6. Verified: django `/api/v1/health/` 200, nginx HTTPS 200, login with restored admin OK (JWT), `/api/v1/projects/` and `/api/v1/repositories/` return the restored demo data.

**Conclusion**: the restore procedure works on a machine with no prior state. Two notes for the runbook:

- **Always run `make migrate` after a restore** — backups capture data as of dump time; migrations applied since (e.g. axes, HNSW index) will be applied on top. The runbook already lists this; the fresh test confirms it is required.
- `restore.sh` referenced an undefined `BACKUP_DIR` in its "Next steps" footer — fixed (defaults to `./backups`).