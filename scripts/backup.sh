#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
[ -f .env ] && . ./.env
set +a

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
REPO_CACHE_VOLUME="${REPO_CACHE_VOLUME:-codecoroner_repo_cache}"
TS="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if ! podman volume exists "$REPO_CACHE_VOLUME" 2>/dev/null; then
    if podman volume exists repo_cache 2>/dev/null; then
        REPO_CACHE_VOLUME=repo_cache
    fi
fi

echo "==> Dumping PostgreSQL database..."
podman exec -e PGPASSWORD="${DB_PASSWORD}" codecoroner-postgres \
    pg_dump -U "${DB_USER:-codecoroner}" -Fc "${DB_NAME:-codecoroner}" \
    > "$BACKUP_DIR/codecoroner-$TS.dump"

echo "==> Archiving repo cache volume (${REPO_CACHE_VOLUME})..."
podman run --rm -v "$REPO_CACHE_VOLUME":/data:ro -v "$PWD/$BACKUP_DIR":/backup:Z \
    docker.io/alpine tar czf "/backup/repos-$TS.tar.gz" -C /data .

echo "==> Retention: removing backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -type f \( -name 'codecoroner-*.dump' -o -name 'repos-*.tar.gz' \) \
    -mtime "+${RETENTION_DAYS}" -delete

echo "==> Backup complete:"
ls -lh "$BACKUP_DIR"