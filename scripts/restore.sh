#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
[ -f .env ] && . ./.env
set +a

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DUMP="${1:-}"
if [ -z "$DUMP" ]; then
    echo "Usage: $0 <dumpfile>"
    ls -lh backups/ 2>/dev/null || true
    exit 1
fi
[ -f "$DUMP" ] || { echo "Dump not found: $DUMP"; exit 1; }

echo "==> Restoring database from $DUMP..."
podman cp "$DUMP" codecoroner-postgres:/tmp/codecoroner_restore.dump
podman exec -e PGPASSWORD="${DB_PASSWORD}" codecoroner-postgres \
    pg_restore --clean --if-exists -U "${DB_USER:-codecoroner}" -d "${DB_NAME:-codecoroner}" \
    /tmp/codecoroner_restore.dump
podman exec codecoroner-postgres rm -f /tmp/codecoroner_restore.dump

echo "==> Database restored."
echo ""
echo "Next steps:"
echo "  1. If you backed up the repo cache, extract repos-<ts>.tar.gz into the repo_cache volume:"
echo "     podman run --rm -v repo_cache:/data -v \"$PWD/$BACKUP_DIR\":/backup:ro alpine tar xzf /backup/repos-<ts>.tar.gz -C /data"
echo "  2. Rebuild/start the stack:  podman-compose up -d"
echo "  3. Apply migrations:         make migrate"
echo "  4. Re-seed base data if needed: make seed"