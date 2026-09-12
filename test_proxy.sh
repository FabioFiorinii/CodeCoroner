#!/bin/sh
echo "=== Test 1: Direct to django ==="
curl -s -X POST -H "Content-Type: application/json" -d @/tmp/login.json http://django:8000/api/v1/auth/login/

echo ""
echo "=== Test 2: Via frontend nginx ==="
curl -s -X POST -H "Content-Type: application/json" -d @/tmp/login.json http://frontend:80/api/v1/auth/login/

echo ""
echo "=== Test 3: Via main nginx ==="
curl -s -X POST -H "Content-Type: application/json" -d @/tmp/login.json http://nginx:80/api/v1/auth/login/
