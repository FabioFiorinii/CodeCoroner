# CodeCoroner — Security Design

## Threat Model

| Threat | Severity | Vector | Mitigation |
|---|---|---|---|
| **Repository code injection** | Critical | Malicious repo in analysis | Sandbox isolation, read-only mounts |
| **Prompt injection** | High | Error context contains prompt escape | Input sanitization, delimiters, validation |
| **Secrets exfiltration via LLM** | High | Code with hardcoded secrets | Secret scanning pre-filter, output audit |
| **SSRF** | High | Git clone from internal services | Allowlist git URLs, network isolation |
| **DoS via large repo** | Medium | Terabyte-size repository | Size limits, timeout, streaming parse |
| **Container escape** | Critical | Sandbox vulnerability | Seccomp, no-cap, no-new-privs, read-only |
| **API abuse** | Medium | Excessive analysis requests | Rate limiting, per-user quotas |
| **Unauthorized access** | High | JWT theft, broken auth | Short-lived tokens, refresh rotation |
| **Data exfiltration** | Medium | Reports contain PII | Output scanning, data retention policy |

## Sandbox Security (Defense in Depth)

```
┌──────────────────────────────────────────────────────────┐
│                    Podman Host                             │
│                                                           │
│  1. Podman runs rootless (user namespace)                  │
│  2. SELinux/AppArmor enforcing                             │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Sandbox Container                                  │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  1. read_only_rootfs: true                    │   │   │
│  │  │  2. cap_drop: ALL                             │   │   │
│  │  │  3. seccomp: custom (block dangerous syscalls) │   │   │
│  │  │  4. no-new-privileges: true                    │   │   │
│  │  │  5. network: none                              │   │   │
│  │  │  6. memory: 2G, pids: 100                      │   │   │
│  │  │  7. tmpfs: /tmp (noexec)                       │   │   │
│  │  │  8. Read-only repo mount                       │   │   │
│  │  │  9. Non-root user (sandbox)                    │   │   │
│  │  │  10. Timeout: 5 minutes (SIGKILL)              │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Seccomp Profile

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "openat", "close",
        "fstat", "stat", "lstat", "newfstatat",
        "mmap", "munmap", "mprotect", "brk",
        "exit_group", "exit", "gettid",
        "clone", "fork", "vfork",
        "execve", "execveat",
        "access", "faccessat", "faccessat2",
        "readlink", "readlinkat",
        "getdents64", "getdents",
        "ioctl", "fcntl", "dup", "dup2", "dup3",
        "pipe", "pipe2", "socketpair"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

## Prompt Injection Prevention

### Multi-Layer Defense

```python
class PromptSanitizer:
    """Sanitize user input before passing to LLM."""

    # Layer 1: Structural delimiters
    DELIMITERS = {
        'system_start': '<|system|>',
        'system_end': '<|/system|>',
        'user_start': '<|user|>',
        'user_end': '<|/user|>',
    }

    # Layer 2: Block known escape patterns
    BLOCKED_PATTERNS = [
        r'<\|\s*(system|user|assistant)\s*\|>',
        r'ignore\s+(all\s+)?(previous|above|below)',
        r'forget\s+(everything|all)',
        r'you\s+are\s+(not\s+)?(an?\s+)?(AI|assistant)',
        r'rewrite\s+(your\s+)?(prompt|instructions|system)',
    ]

    # Layer 3: Encode user content
    @staticmethod
    def encode_user_content(content: str) -> str:
        """Wrap user content in secure XML-like tags."""
        # Remove any existing delimiters
        for delim in PromptSanitizer.DELIMITERS.values():
            content = content.replace(delim, '')

        # Strip control characters
        content = ''.join(c for c in content if c.isprintable() or c in '\n\r\t')

        return content

    @staticmethod
    def build_secure_prompt(system_prompt: str, user_content: str) -> str:
        clean = PromptSanitizer.encode_user_content(user_content)
        return f"""{system_prompt}

---BEGIN USER INPUT---
{clean}
---END USER INPUT---
"""
```

### LLM Output Validation

```python
class OutputValidator:
    """Validate LLM output before processing."""

    @staticmethod
    def extract_json(text: str) -> dict:
        """Extract and validate JSON from LLM response."""

        # Find JSON block (handle ```json ... ``` or raw)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            # Try to find {...} directly
            brace_match = re.search(r'\{.*\}', text, re.DOTALL)
            if brace_match:
                text = brace_match.group()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("LLM output is not valid JSON")

        # Validate expected keys exist
        if not isinstance(data, dict):
            raise ValueError("LLM output is not a dictionary")

        return data

    @staticmethod
    def sanitize_diff(patch_diff: str) -> str:
        """Remove any shell commands or dangerous content from diff."""
        lines = patch_diff.split('\n')
        clean = []
        for line in lines:
            if line.startswith('rm ') or line.startswith('sudo '):
                continue  # Skip dangerous commands
            if '`' in line and not line.startswith('+'):
                continue  # Skip inline code in non-added lines
            clean.append(line)
        return '\n'.join(clean)
```

## Secrets Management

### Policy

1. **Never store secrets in code** — use environment variables
2. **Never commit .env files** — `.env` in `.gitignore`
3. **All secrets encrypted at rest** — Django encrypted fields for DB
4. **All traffic encrypted in transit** — HTTPS via nginx, internal HTTP only
5. **Secrets rotation** — Automate via `django-clock` for periodic rotation

### Environment Variables (Production)

```
DJANGO_SECRET_KEY=<256-bit-random>
DB_PASSWORD=<64-char-random>
REDIS_PASSWORD=<64-char-random>
MINIO_ROOT_USER=codecoroner
MINIO_ROOT_PASSWORD=<64-char-random>
OLLAMA_API_KEY=<optional>
SENTRY_DSN=<sentry-dsn>
```

### Git Secrets Detection

```yaml
# .pre-commit-config.yaml (additional hook)
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

## Authentication & Authorization

### JWT Strategy

```python
# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('DJANGO_SECRET_KEY'),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### Role-Based Access Control (RBAC)

```python
class Role(IntEnum):
    VIEWER = 10   # Read-only
    MEMBER = 20   # Create analyses
    ADMIN = 30    # Manage members
    OWNER = 40    # Delete project, transfer

    @classmethod
    def can(cls, role: 'Role', permission: str) -> bool:
        permissions = {
            'view_project': {VIEWER, MEMBER, ADMIN, OWNER},
            'create_analysis': {MEMBER, ADMIN, OWNER},
            'manage_members': {ADMIN, OWNER},
            'delete_project': {OWNER},
            'view_reports': {VIEWER, MEMBER, ADMIN, OWNER},
        }
        return role in permissions.get(permission, set())
```

### API Rate Limiting

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
        'analyses.throttling.AnalysisRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '200/hour',
        'anon': '20/hour',
        'analysis': '10/hour',  # Analyses per user per hour
        'index': '5/hour',      # Repository indexes per hour
    }
}
```

## Data Protection

| Data Type | Storage | Encryption | Retention |
|---|---|---|---|
| User credentials | PostgreSQL | bcrypt hashed | Until account deletion |
| API tokens | PostgreSQL | SHA-256 hashed | Revoked + 30 days |
| Repository code | Filesystem | Disk encryption | Until project deletion |
| Code embeddings | PostgreSQL (pgvector) | Disk encryption | Until project deletion |
| Analysis results | PostgreSQL | Disk encryption | 90 days (auto-cleanup) |
| Reports | MinIO (S3) | Server-side encryption | 90 days |
| Logs | stdout → journald | N/A | 30 days (log rotation) |

## Repository Isolation

```python
class RepositoryIsolation:
    """Ensure one analysis cannot affect another's repository."""

    @staticmethod
    def clone_path(repo_id: UUID) -> Path:
        """Each repo clone is isolated by ID."""
        return REPO_CACHE_DIR / str(repo_id)

    @staticmethod
    def sandbox_mount(repo_id: UUID) -> str:
        """Sandbox mount is read-only and isolated."""
        return f"{REPO_CACHE_DIR / str(repo_id)}:/repo:ro,Z"

    @staticmethod
    def verify_git_url(url: str) -> bool:
        """Only allow known-safe git URL patterns."""
        allowed_prefixes = [
            'https://github.com/',
            'https://gitlab.com/',
            'https://bitbucket.org/',
            'git@github.com:',
            'git@gitlab.com:',
        ]
        return any(url.startswith(prefix) for prefix in allowed_prefixes)
```

## Audit Logging

```python
# Structured logging with structlog
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            '()': 'structlog.stdlib.ProcessorFormatter',
            'processor': structlog.processors.JSONRenderer(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'codecoroner': { 'handlers': ['console'], 'level': 'INFO' },
        'codecoroner.security': { 'handlers': ['console'], 'level': 'WARNING' },
    },
}
```

Every security-relevant event is logged with:
- Event type
- User ID
- IP address
- Timestamp
- Resource ID
- Action
- Success/failure
