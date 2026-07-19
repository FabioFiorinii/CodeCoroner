# CodeCoroner — CI/CD Pipeline

## Pipeline Overview

```
┌─────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌─────────┐
│  Lint   │──▶│  Test  │──▶│  Build │──▶│  Scan  │──▶│ Deploy  │
│  ruff   │   │ pytest │   │ podman │   │ trivy  │   │ compose │
│  mypy   │   │  cov   │   │  img   │   │  snyk  │   │   or    │
│  eslint │   │        │   │        │   │        │   │  k8s    │
└─────────┘   └────────┘   └────────┘   └────────┘   └─────────┘
```

## GitHub Actions Workflow (CI)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint-backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: pip
      - run: pip install -r requirements-dev.txt
      - run: ruff check . --output-format=github
      - run: ruff format . --check
      - run: mypy . --strict

  lint-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test-backend:
    needs: lint-backend
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: codecoroner_test
          POSTGRES_USER: codecoroner
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: pip
      - run: pip install -r requirements-dev.txt
      - run: |
          pytest \
            --cov=. \
            --cov-report=xml \
            --cov-report=term-missing \
            --ds=config.settings.test \
            -v
      - uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  test-frontend:
    needs: lint-frontend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
      - run: npm ci
      - run: npm run test -- --coverage
      - uses: codecov/codecov-action@v4
        with:
          directory: frontend/coverage

  build-images:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: podman/login-action@v1
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - run: podman build -t ghcr.io/${{ github.repository }}/backend:${{ github.sha }} -f backend/Dockerfile backend/
      - run: podman build -t ghcr.io/${{ github.repository }}/ai-engine:${{ github.sha }} -f ai-engine/Dockerfile ai-engine/
      - run: |
          podman push ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          podman push ghcr.io/${{ github.repository }}/ai-engine:${{ github.sha }}
      - run: |
          podman tag ghcr.io/${{ github.repository }}/backend:${{ github.sha }} ghcr.io/${{ github.repository }}/backend:latest
          podman push ghcr.io/${{ github.repository }}/backend:latest
          podman tag ghcr.io/${{ github.repository }}/ai-engine:${{ github.sha }} ghcr.io/${{ github.repository }}/ai-engine:latest
          podman push ghcr.io/${{ github.repository }}/ai-engine:latest

  security-scan:
    needs: build-images
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          podman run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            ghcr.io/aquasecurity/trivy:latest \
            image --severity HIGH,CRITICAL \
            ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
```

## CD Pipeline (GitHub Actions - Deploy)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]

jobs:
  deploy-prod:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            cd /opt/codecoroner
            git pull
            podman-compose pull
            podman-compose up -d --force-recreate
            podman image prune -f
```

## Local Development Workflow

```bash
# Start all services
podman-compose up -d

# Run migrations
podman-compose exec django python manage.py migrate

# Create superuser
podman-compose exec django python manage.py createsuperuser

# Watch logs
podman-compose logs -f django celery_worker

# Run tests
podman-compose exec django pytest

# Rebuild single service
podman-compose build django && podman-compose up -d django
```

## Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [django-stubs, pydantic]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [javascript, typescript, css, json, markdown]
```

## Quality Gates

| Gate | Tool | Threshold | Action |
|---|---|---|---|
| Code style | ruff | 0 errors | Block PR |
| Type checking | mypy | 0 errors | Block PR |
| Backend tests | pytest | >90% cov | Warning if <90% |
| Frontend tests | vitest | >80% cov | Warning if <80% |
| Security scan | trivy | 0 CRITICAL | Block PR |
| No secrets | detect-secrets | 0 findings | Block PR |
| No large files | pre-commit | <1MB | Block PR |
