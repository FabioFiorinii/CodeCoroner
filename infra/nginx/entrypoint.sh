#!/bin/sh
set -e

CERT_DIR=/etc/nginx/certs
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/server.crt" ] || [ ! -f "$CERT_DIR/server.key" ]; then
    command -v openssl >/dev/null 2>&1 || apk add --no-cache openssl >/dev/null 2>&1
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.crt" \
        -subj "/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,DNS:codecoroner.local,IP:127.0.0.1" >/dev/null 2>&1
    echo "Generated self-signed certificate in $CERT_DIR"
fi

if [ "${ENABLE_HSTS:-false}" = "true" ]; then
    echo 'add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;' \
        > /etc/nginx/hsts.conf
else
    : > /etc/nginx/hsts.conf
fi

exec nginx -g 'daemon off;'