#!/usr/bin/env bash
# CodeCoroner guided install — idempotent, safe to re-run.
# Usage: bash scripts/install.sh [--prod]
#   default : dev stack  (.env, podman-compose.yml)
#   --prod  : prod stack (.env.prod, podman-compose.yml + podman-compose.prod.yml)
# Never deletes volumes or images. For a full wipe see `make clean` (destructive).
set -euo pipefail

cd "$(dirname "$0")/.."

MODE="dev"
if [ "${1:-}" = "--prod" ]; then
    MODE="prod"
elif [ -n "${1:-}" ]; then
    echo "Usage: bash scripts/install.sh [--prod]" >&2
    exit 2
fi

if [ "$MODE" = "prod" ]; then
    ENV_FILE=".env.prod"
    ENV_TEMPLATE=".env.prod.example"
    COMPOSE_FILES="-f podman-compose.yml -f podman-compose.prod.yml"
else
    ENV_FILE=".env"
    ENV_TEMPLATE=".env.example"
    COMPOSE_FILES="-f podman-compose.yml"
fi

# --- 1. prerequisites -------------------------------------------------------
missing=0
for bin in podman openssl; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        echo "ERROR: required binary '$bin' not found in PATH." >&2
        missing=1
    fi
done
if command -v podman-compose >/dev/null 2>&1; then
    COMPOSE="podman-compose"
elif podman compose version >/dev/null 2>&1; then
    COMPOSE="podman compose"
else
    echo "ERROR: neither 'podman-compose' nor 'podman compose' is available." >&2
    missing=1
fi
if [ "$missing" -ne 0 ]; then exit 1; fi
echo "==> prerequisites ok (podman + compose + openssl)"

# --- 2. env file ------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    echo "==> created $ENV_FILE from $ENV_TEMPLATE"
fi

# Replace CHANGE_ME_* placeholders with fresh secrets (existing values kept).
set_secret() {
    local key="$1" bytes="$2" value
    if grep -q "^${key}=CHANGE_ME" "$ENV_FILE"; then
        value="$(openssl rand -hex "$bytes")"
        sed -i "s/^${key}=CHANGE_ME.*/${key}=${value}/" "$ENV_FILE"
        echo "==> generated secret for $key"
    fi
}
if [ "$MODE" = "prod" ]; then
    cp "$ENV_FILE" "$ENV_FILE.bak"
    set_secret DJANGO_SECRET_KEY 32
    set_secret DB_PASSWORD 32
    set_secret MINIO_PASSWORD 16
    if grep -q "CHANGE_ME" "$ENV_FILE"; then
        echo "ERROR: $ENV_FILE still contains CHANGE_ME placeholders. Fill them, then re-run." >&2
        exit 1
    fi
fi

# shellcheck disable=SC1090
set -a
# shellcheck disable=SC1091
. ./"$ENV_FILE"
set +a
HTTP_PORT="${HTTP_PORT:-8080}"
HTTPS_PORT="${HTTPS_PORT:-8443}"

# --- 3. ports ----------------------------------------------------------------
for port in "$HTTP_PORT" "$HTTPS_PORT"; do
    if (command -v ss >/dev/null 2>&1 && ss -tln | grep -q ":${port} ") \
        || (command -v netstat >/dev/null 2>&1 && netstat -tln 2>/dev/null | grep -q ":${port} "); then
        echo "WARNING: port $port already in use — nginx may fail to start." >&2
    fi
done

# --- 4. build + start (volumes are never deleted here) -----------------------
# shellcheck disable=SC2086
$COMPOSE $COMPOSE_FILES up -d --build
echo "==> stack starting..."

# --- 5. wait for the API -----------------------------------------------------
HEALTH_URL="http://127.0.0.1:8000/api/v1/health/"
ready=0
for _ in $(seq 1 60); do
    if command -v curl >/dev/null 2>&1 && curl -sf --max-time 5 "$HEALTH_URL" >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 10
done
if [ "$ready" -ne 1 ]; then
    echo "WARNING: API not reachable at $HEALTH_URL yet — continuing anyway." >&2
    echo "Check progress with: $COMPOSE $COMPOSE_FILES ps / logs" >&2
fi

# --- 6. migrate + seed (both idempotent) -------------------------------------
# shellcheck disable=SC2086
$COMPOSE $COMPOSE_FILES exec django python manage.py migrate
# shellcheck disable=SC2086
$COMPOSE $COMPOSE_FILES exec django python manage.py seed_base || true

echo ""
echo "==> Install complete ($MODE)."
echo "    Frontend : https://localhost:${HTTPS_PORT} (http://localhost:${HTTP_PORT} redirects)"
echo "    API      : http://localhost:8000/api/v1/   (localhost only)"
echo "    Next     : tune TLS (CERT_MODE in $ENV_FILE, see README 'TLS scenarios'),"
echo "               then schedule backups (scripts/backup-restore.md)."
