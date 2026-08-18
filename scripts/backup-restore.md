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