#!/bin/bash
# Test user registration
curl -s -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","username":"admin","password":"testpass123"}'
echo ""
