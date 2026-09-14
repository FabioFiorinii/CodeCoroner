#!/usr/bin/env bash
# CodeCoroner minimal watchdog — cron-safe, no new dependencies.
# Exit 0 = all ok (silent-friendly), exit 1 = at least one ALARM.
# Usage: bash scripts/healthcheck.sh [--prod]
#   --prod uses .env.prod + the prod compose files; default uses .env.
# Suggested cron (every 15 min):
#   */15 * * * * bash /path/to/codecoroner/scripts/healthcheck.sh >> /var/log/codecoroner-health.log 2>&1
set -uo pipefail

cd "$(dirname "$0")/.."

if [ "${1:-}" = "--prod" ]; then
    ENV_FILE=".env.prod"
    COMPOSE_FILES="-f podman-compose.yml -f podman-compose.prod.yml"
elif [ -z "${1:-}" ]; then
    ENV_FILE=".env"
    COMPOSE_FILES="-f podman-compose.yml"
else
    echo "Usage: bash scripts/healthcheck.sh [--prod]" >&2
    exit 2
fi

if command -v podman-compose >/dev/null 2>&1; then
    COMPOSE="podman-compose"
else
    COMPOSE="podman compose"
fi

if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . ./"$ENV_FILE"
    set +a
fi
BIND="${BIND_ADDR:-127.0.0.1}"
HTTP_PORT="${HTTP_PORT:-8080}"
HTTPS_PORT="${HTTPS_PORT:-8443}"
CERT_MODE="${CERT_MODE:-selfsigned}"
DLQ_THRESHOLD="${DLQ_ALERT_THRESHOLD:-5}"

failures=0
ok() { echo "OK: $1"; }
alarm() { echo "ALARM: $1"; failures=$((failures + 1)); }

# --- 1. Django API -----------------------------------------------------------
if command -v curl >/dev/null 2>&1 && curl -sf --max-time 10 "http://${BIND}:8000/api/v1/health/" >/dev/null 2>&1; then
    ok "django api"
else
    alarm "django api unreachable (http://${BIND}:8000/api/v1/health/)"
fi

# --- 2. AI engine ------------------------------------------------------------
if command -v curl >/dev/null 2>&1 && curl -sf --max-time 10 "http://${BIND}:8002/health" >/dev/null 2>&1; then
    ok "ai-engine"
else
    alarm "ai-engine unreachable (http://${BIND}:8002/health)"
fi

# --- 3. nginx front door -----------------------------------------------------
if [ "$CERT_MODE" = "behind-proxy" ]; then
    FRONT_URL="http://${BIND}:${HTTP_PORT}/"
    CURL_FLAGS="-sf --max-time 10"
else
    FRONT_URL="https://${BIND}:${HTTPS_PORT}/"
    CURL_FLAGS="-sfk --max-time 10"
fi
if command -v curl >/dev/null 2>&1 && curl $CURL_FLAGS "$FRONT_URL" >/dev/null 2>&1; then
    ok "nginx front door ($FRONT_URL)"
else
    alarm "nginx front door unreachable ($FRONT_URL)"
fi

# --- 4. Celery workers alive -------------------------------------------------
# NOTE: no -T flag (not supported by all podman versions); grep matches anyway.
# shellcheck disable=SC2086
if $COMPOSE $COMPOSE_FILES exec celery_worker celery -A config.celery inspect ping 2>/dev/null | grep -q pong; then
    ok "celery workers"
else
    alarm "no celery worker answered inspect ping"
fi

# --- 5. Dead-letter queue depth ----------------------------------------------
# shellcheck disable=SC2086
dlq_out="$($COMPOSE $COMPOSE_FILES exec django python manage.py dlq count 2>/dev/null || echo 'DLQ entries: unknown')"
dlq_n="$(echo "$dlq_out" | grep -oE '[0-9]+' | tail -n 1)"
if [ -z "$dlq_n" ]; then
    alarm "could not read DLQ count ($dlq_out)"
elif [ "$dlq_n" -gt "$DLQ_THRESHOLD" ]; then
    alarm "DLQ depth $dlq_n exceeds threshold $DLQ_THRESHOLD (manage.py dlq list)"
else
    ok "dlq depth $dlq_n (threshold $DLQ_THRESHOLD)"
fi

# --- 6. Backup dir disk usage ------------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-./backups}"
if [ -d "$BACKUP_DIR" ]; then
    use_pct="$(df -P "$BACKUP_DIR" | awk 'NR==2 {gsub(/%/, ""); print $5}')"
    if [ -n "$use_pct" ] && [ "$use_pct" -ge 90 ]; then
        alarm "disk usage ${use_pct}% on backup dir $BACKUP_DIR"
    else
        ok "disk usage ${use_pct:-?}% on backup dir"
    fi
else
    alarm "backup dir $BACKUP_DIR missing (no backups ever taken?)"
fi

if [ "$failures" -ne 0 ]; then
    echo "RESULT: $failures check(s) alarming"
    exit 1
fi
echo "RESULT: all checks ok"
