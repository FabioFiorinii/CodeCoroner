#!/bin/sh
set -e

# CERT_MODE selects how TLS is handled:
#   selfsigned   generate a self-signed cert on first start (dev/test only)
#   byo          use customer certs pre-mounted into the nginx_certs volume
#                (server.crt + server.key); fail fast if they are missing
#   behind-proxy serve plain HTTP only; TLS/HSTS live on the customer's
#                own reverse proxy upstream
CERT_DIR=/etc/nginx/certs
CONF_SRC=/etc/nginx/conf-src
HTTPS_PORT="${HTTPS_PORT:-8443}"
CERT_MODE="${CERT_MODE:-selfsigned}"

case "$HTTPS_PORT" in
    ''|*[!0-9]*)
        echo "ERROR: HTTPS_PORT must be numeric, got '$HTTPS_PORT'" >&2
        exit 1
        ;;
esac

mkdir -p "$CERT_DIR"

case "$CERT_MODE" in
    behind-proxy)
        cp "$CONF_SRC/nginx-behind-proxy.conf" /etc/nginx/nginx.conf
        ;;
    byo|selfsigned|*)
        if [ ! -f "$CERT_DIR/server.crt" ] || [ ! -f "$CERT_DIR/server.key" ]; then
            if [ "$CERT_MODE" = "byo" ]; then
                echo "ERROR: CERT_MODE=byo but no server.crt/server.key in $CERT_DIR (nginx_certs volume)." >&2
                echo 'Mount your certificate and key into the nginx_certs volume first.' >&2
                exit 1
            fi
            command -v openssl >/dev/null 2>&1 || apk add --no-cache openssl >/dev/null 2>&1
            openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
                -keyout "$CERT_DIR/server.key" \
                -out "$CERT_DIR/server.crt" \
                -subj "/CN=localhost" \
                -addext "subjectAltName=DNS:localhost,DNS:codecoroner.local,IP:127.0.0.1" >/dev/null 2>&1
            echo "Generated self-signed certificate in $CERT_DIR"
        fi
        sed "s/__HTTPS_PORT__/$HTTPS_PORT/g" "$CONF_SRC/nginx.conf" > /etc/nginx/nginx.conf
        ;;
esac

if [ "${ENABLE_HSTS:-false}" = "true" ]; then
    echo 'add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;' \
        > /etc/nginx/hsts.conf
else
    : > /etc/nginx/hsts.conf
fi

nginx -t -c /etc/nginx/nginx.conf
exec nginx -g 'daemon off;'
