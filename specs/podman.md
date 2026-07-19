# CodeCoroner — Podman Architecture

## Container Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Podman Host (Ubuntu 24.04)                       │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    podman_net (172.20.0.0/16)                     │   │
│  │                                                                   │   │
│  │  ┌────────────┐    ┌────────────┐    ┌────────────┐              │   │
│  │  │ reverse-proxy │    │ django      │    │ postgres    │              │   │
│  │  │ nginx:latest │    │ gunicorn    │    │ pgvector    │              │   │
│  │  │ :8080 → :8000 │    │ :8000       │    │ :5432       │              │   │
│  │  └────────────┘    └──────┬──────┘    └────────────┘              │   │
│  │                           │                                        │   │
│  │  ┌────────────┐    ┌──────▼──────┐    ┌────────────┐              │   │
│  │  │ redis:7    │    │ celery_worker│    │ ollama      │              │   │
│  │  │ :6379      │    │ (scalable)  │    │ :11434      │              │   │
│  │  └────────────┘    └──────┬──────┘    └────────────┘              │   │
│  │                           │                                        │   │
│  │  ┌────────────┐    ┌──────▼──────┐    ┌────────────┐              │   │
│  │  │ minio       │    │ ai-engine   │    │ sandbox     │              │   │
│  │  │ :9000       │    │ (agents)    │    │ (ephemeral) │              │   │
│  │  │ (artifacts) │    │             │    │             │              │   │
│  │  └────────────┘    └────────────┘    └────────────┘              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Volumes:                                                               │
│    pg_data        → /var/lib/postgresql/data                            │
│    redis_data     → /data                                               │
│    minio_data     → /data                                               │
│    ollama_models  → /root/.ollama                                       │
│    repo_cache     → /repositories                                       │
│    static_volume  → /static                                             │
│    media_volume   → /media                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Podman Compose (MVP)

```yaml
# podman-compose.yml
version: "3.9"

networks:
  codecoroner_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  pg_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local
  ollama_models:
    driver: local
  repo_cache:
    driver: local
  static_volume:
    driver: local
  media_volume:
    driver: local

services:
  reverse-proxy:
    image: docker.io/nginx:alpine
    ports:
      - "8080:80"
      - "443:443"
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro,Z
      - ./infra/nginx/ssl:/etc/nginx/ssl:ro,Z
      - static_volume:/static:ro,Z
      - media_volume:/media:ro,Z
    depends_on:
      - django
    networks:
      - codecoroner_net
    restart: unless-stopped

  postgres:
    image: docker.io/pgvector/pgvector:pg16
    volumes:
      - pg_data:/var/lib/postgresql/data:Z
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    environment:
      POSTGRES_DB: codecoroner
      POSTGRES_USER: codecoroner
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
    networks:
      - codecoroner_net
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U codecoroner"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: docker.io/redis:7-alpine
    volumes:
      - redis_data:/data:Z
    networks:
      - codecoroner_net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  django:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - static_volume:/app/static:Z
      - media_volume:/app/media:Z
      - repo_cache:/repositories:Z
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      DATABASE_URL: postgres://codecoroner:${DB_PASSWORD:?required}@postgres:5432/codecoroner
      REDIS_URL: redis://redis:6379/0
      OLLAMA_BASE_URL: http://ollama:11434
      CELERY_BROKER_URL: redis://redis:6379/1
      SECRET_KEY: ${DJANGO_SECRET_KEY:?required}
      ALLOWED_HOSTS: ${ALLOWED_HOSTS:-localhost}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - codecoroner_net
    restart: unless-stopped

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A config.celery worker -l INFO --concurrency=2
    volumes:
      - repo_cache:/repositories:Z
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      DATABASE_URL: postgres://codecoroner:${DB_PASSWORD:?required}@postgres:5432/codecoroner
      REDIS_URL: redis://redis:6379/0
      OLLAMA_BASE_URL: http://ollama:11434
      CELERY_BROKER_URL: redis://redis:6379/1
      SECRET_KEY: ${DJANGO_SECRET_KEY:?required}
    depends_on:
      - django
      - redis
    networks:
      - codecoroner_net
    restart: unless-stopped
    deploy:
      replicas: 2

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A config.celery beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      DATABASE_URL: postgres://codecoroner:${DB_PASSWORD:?required}@postgres:5432/codecoroner
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
      SECRET_KEY: ${DJANGO_SECRET_KEY:?required}
    depends_on:
      - django
      - redis
    networks:
      - codecoroner_net
    restart: unless-stopped

  ollama:
    image: docker.io/ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama:Z
    environment:
      OLLAMA_HOST: 0.0.0.0
    networks:
      - codecoroner_net
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]  # GPU passthrough if available

  ai-engine:
    build:
      context: ./ai-engine
      dockerfile: Dockerfile
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      DATABASE_URL: postgres://codecoroner:${DB_PASSWORD:?required}@postgres:5432/codecoroner
      REDIS_URL: redis://redis:6379/0
      LOG_LEVEL: INFO
    volumes:
      - repo_cache:/repositories:ro,Z
    depends_on:
      - ollama
      - postgres
    networks:
      - codecoroner_net
    restart: unless-stopped

  minio:
    image: docker.io/minio/minio:latest
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data:Z
    environment:
      MINIO_ROOT_USER: ${MINIO_USER:-codecoroner}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD:?required}
    networks:
      - codecoroner_net
    restart: unless-stopped

  # Optional: only for development
  pgadmin:
    image: docker.io/dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@codecoroner.dev
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
    networks:
      - codecoroner_net
    profiles:
      - dev
```

## Sandbox Container (Code Execution)

### Design

```yaml
# sandbox/podman-compose.yml  (dynamically generated per analysis)
services:
  sandbox:
    image: codecoroner/sandbox:latest
    # Built from sandbox/Dockerfile
    # Contains: python, node, gcc, go, rust, etc.
    volumes:
      - repo_cache:/repo:ro,Z  # Read-only source
      - sandbox_tmp:/tmp:Z     # Temp workspace
    environment:
      SANDBOX_ID: ${SANDBOX_ID}
      ANALYSIS_ID: ${ANALYSIS_ID}
    # Security
    cap_drop:
      - ALL
    cap_add: []  # No capabilities
    security_opt:
      - no-new-privileges=true
      - seccomp=sandbox/seccomp-default.json
    read_only_rootfs: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100M
      - /var/tmp:noexec,nosuid,size=100M
      - /run:noexec,nosuid,size=50M
    network: none  # No network access
    cpu_shares: 512
    memory: 2g
    memory-swap: 2g  # No swap
    pids_limit: 100
    stop_signal: SIGKILL
    stop_grace_period: 30s

networks: {}
```

### Sandbox Dockerfile

```dockerfile
FROM docker.io/python:3.13-slim AS base

# Install runtime dependencies for multiple languages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nodejs \
    npm \
    golang-go \
    rustc \
    cargo \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Python tools
RUN pip install --no-cache-dir \
    pytest \
    ruff \
    mypy \
    pytest-cov

# Create sandbox user (non-root)
RUN useradd -r -s /bin/false sandbox
USER sandbox
WORKDIR /workspace

# Copy test scripts
COPY --chown=sandbox:sandbox scripts/ /usr/local/bin/
```

## Security Measures

| Measure | Implementation |
|---|---|
| **No capabilities** | `cap_drop: [ALL]`, `cap_add: []` |
| **No new privileges** | `security_opt: no-new-privileges=true` |
| **Seccomp** | Custom seccomp profile blocking dangerous syscalls |
| **Read-only rootfs** | `read_only_rootfs: true` |
| **No network** | `network: none` |
| **Memory limit** | `memory: 2g`, `memory-swap: 2g` |
| **CPU limit** | `cpu_shares: 512` (proportional) |
| **PID limit** | `pids_limit: 100` (prevents fork bombs) |
| **No new privs** | Kernel security |
| **Read-only source** | Repo mounted `:ro,Z` |
| **Ephemeral** | Container destroyed after validation |
| **SELinux** | `:Z` labels for volume mounts |

## Networks

```
codecoroner_net (internal)
  ├── reverse-proxy    :80, :443  → exposed
  ├── django           :8000       → internal only
  ├── postgres         :5432       → internal only
  ├── redis            :6379       → internal only
  ├── ollama           :11434      → internal only
  ├── celery_worker    :none       → internal only
  ├── ai-engine        :none       → internal only
  └── minio            :9000, :9001 → internal only

Sandbox containers: no network
```

## Volume Strategy

| Volume | Purpose | Access | Backup |
|---|---|---|---|
| `pg_data` | Database persistence | RW | Yes (pg_dump) |
| `redis_data` | Cache persistence | RW | Optional |
| `minio_data` | Artifact storage | RW | Yes |
| `ollama_models` | AI model weights | RW | No (re-download) |
| `repo_cache` | Cloned repositories | RW (django, celery) | No |
| | | RO (sandbox) | |
| `static_volume` | Django staticfiles | RW (django), RO (nginx) | No |
| `media_volume` | User uploads | RW (django) | Yes |

## Build Process

```dockerfile
# backend/Dockerfile
FROM docker.io/python:3.13-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM docker.io/python:3.13-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

```dockerfile
# ai-engine/Dockerfile
FROM docker.io/python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app
CMD ["python", "-m", "agents.agent_server"]
```
