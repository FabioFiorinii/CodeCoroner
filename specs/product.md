# CodeCoroner — Product Breakdown

## Vision

CodeCoroner is an AI-native debugging platform that transforms how developers investigate and resolve software defects. Instead of manually combing through logs, stacktraces, and source code, engineers submit an error context and receive a fully analyzed root cause, a validated patch, and a comprehensive report — all generated automatically by a pipeline of specialized AI agents.

## Mission

Make root cause analysis and automated patching accessible, reliable, and reproducible for any codebase, regardless of language or scale. Reduce mean-time-to-resolution (MTTR) from hours or days to minutes.

## Target Audience

| Persona | Need | Value Proposition |
|---|---|---|
| **Individual Developer** | Fast bug fix without context-switching | Submit error, get patch, move on |
| **Engineering Team** | Reduce debugging overhead in sprints | Automated RCA in CI/CD post-mortems |
| **DevOps/SRE** | Incident response automation | Correlate logs + code automatically |
| **OSS Maintainer** | Triage and fix issues faster | Patch candidates from bug reports |
| **QA Engineer** | Reproduce and localize bugs | Stacktrace-to-code mapping |

## Core Capabilities (MVP: Bug Localization + RCA)

### 1. Repository Ingestion

- Clone/pull Git repositories
- Parse repository structure (multi-language via Tree-sitter)
- Build an in-memory + persisted code graph
- Support partial/selective indexing (file-level)

### 2. Knowledge Base Construction

- Chunk source code into semantic units (functions, classes, blocks)
- Generate embeddings locally via Ollama
- Store chunks + embeddings in pgvector
- Maintain function call graph, import graph, class hierarchy

### 3. Bug Localization

- Accept: stacktrace, log snippets, error reports, natural language description
- Retrieve relevant code chunks via hybrid search (semantic + BM25)
- Score files by suspicion probability
- Return ranked list of candidate files + line ranges

### 4. Root Cause Analysis

- Analyze retrieved code chunks with Ollama LLM
- Trace call paths and data flow
- Identify likely root cause with reasoning chain
- Generate structured RCA report

### 5. Reporting

- Format RCA as structured document
- Include: error summary, suspect files, trace chain, probable cause, evidence snippets

## Post-MVP Capabilities

### V1 — Patch Generation

- Generate candidate patches via LLM
- Run static analysis (ruff, mypy) on patch
- Execute tests in isolated Podman sandbox
- Score patch quality (pass rate, style compliance)

### V2 — Advanced Features

- Multi-project dashboards
- CI/CD integration (GitHub Actions, GitLab CI)
- Historical trend analysis of recurring bugs
- Team collaboration (shared investigations)

### V3 — Enterprise

- OpenAPI/Anthropic/Gemini support (beyond Ollama)
- On-premise deployment
- SSO/RBAC
- Audit logging
- SLA-graded execution tiers
- MicroVM isolation
- Custom agent pipelines

## Competitive Landscape

| Tool | Approach | Gap |
|---|---|---|
| **Sentinel** | Observability + APM | No code-level RCA |
| **Sentry** | Error tracking + stacktrace | No patch generation |
| **GitHub Copilot** | Code generation in IDE | No debugging pipeline |
| **RCA (IBM/ServiceNow)** | ITSM + runbooks | Rigid, not AI-native |
| **Debugger AI (incumbent)** | Chat over codebase | No multi-step pipeline |

**CodeCoroner differentiator**: purpose-built, multi-agent pipeline that does not just chat about the bug — it systematically localizes, analyzes, and resolves it.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **AI execution** | Ollama local | Privacy, zero API cost, offline capable |
| **Multi-language AST** | Tree-sitter | One parser per language, extensible |
| **Vector storage** | pgvector | Same DB as operational data, no extra infra |
| **Code chunking** | Semantic (AST-based) | Better retrieval than naive line splits |
| **Task queue** | Celery + Redis | Mature, well-documented, Django integration |
| **Container runtime** | Podman | Rootless, daemonless, K8s-compatible |
| **Sandbox execution** | Podman containers | Sufficient for MVP, upgradeable to microVM |
| **Frontend** | React + Vite + TypeScript | Fast dev loop, type safety |
| **Backend** | Django + DRF | Batteries included, admin, ORM, auth |

## Business Model (Future)

- **Free Tier**: 1 project, 50 analyses/month, community models
- **Pro Tier**: Unlimited projects, priority queue, API access
- **Enterprise Tier**: On-prem, SSO, custom models, SLA

## Success Metrics

| Metric | Target (MVP) |
|---|---|
| Bug localization accuracy (Top-3 files) | >80% |
| RCA quality (human-evaluated plausible) | >70% |
| Average analysis time | <5 min |
| False positive rate (files flagged wrongly) | <15% |
| User retention (weekly active) | >40% |
