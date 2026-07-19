# CodeCoroner — Domain Driven Design

## Bounded Contexts

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CODEGORONER SYSTEM                                    │
│                                                                          │
│  ┌─────────────────────┐  ┌─────────────────────┐                       │
│  │     Identity         │  │    Project           │                      │
│  │  & Access Context    │  │  Management Context   │                     │
│  │                      │  │                      │                       │
│  │  Bounded Context:    │  │  Bounded Context:    │                       │
│  │  - User registration │  │  - Repository CRUD   │                       │
│  │  - Authentication    │  │  - Project config    │                       │
│  │  - Authorization     │  │  - Language support   │                       │
│  │  - API tokens        │  │  - Member roles      │                       │
│  └──────────┬───────────┘  └──────────┬──────────┘                       │
│             │                         │                                  │
│             │   ┌─────────────────────▼──────────────────────┐           │
│             │   │          Analysis Context                    │           │
│             │   │  Core Domain — The heart of the system      │           │
│             │   │                                               │         │
│             │   │  - Repository Indexing (Sub-domain)           │         │
│             │   │  - Bug Localization (Sub-domain)              │         │
│             │   │  - Root Cause Analysis (Sub-domain)           │         │
│             │   │  - Patch Generation (Sub-domain)              │         │
│             │   │  - Validation & Testing (Sub-domain)          │         │
│             │   │  - Report Generation (Sub-domain)             │         │
│             │   └───────────────────────────────────────────────┘         │
│             │                         │                                  │
│  ┌──────────▼───────────┐  ┌─────────▼───────────┐                      │
│  │   Sandbox Context     │  │   Integration Context │                     │
│  │                       │  │                       │                    │
│  │  - Container mgmt    │  │  - Webhooks           │                    │
│  │  - Execution env     │  │  - CI/CD connectors   │                    │
│  │  - Test running       │  │  - API clients         │                    │
│  │  - Isolation policies │  │  - Event publishing   │                    │
│  └───────────────────────┘  └───────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Ubiquitous Language

| Term | Definition |
|---|---|
| **Analysis** | A complete investigation from input to report |
| **AnalysisRun** | A single execution of the analysis pipeline |
| **Repository** | A Git-managed source code project |
| **CodeChunk** | A semantic unit of code (function, class, block) |
| **Embedding** | Vector representation of a code chunk |
| **ErrorContext** | Logs, stacktrace, and description of a bug |
| **SuspicionScore** | Float probability that a file contains the bug |
| **RootCause** | The identified origin of the defect |
| **Patch** | A git diff proposing a fix |
| **PatchValidation** | Score from tests + static analysis |
| **Report** | Structured document with findings |
| **Agent** | Specialized AI component performing one task |

## Aggregates

### Aggregate: Project

```
Project
├── id: UUID
├── name: String
├── description: Text
├── language: String[]
├── created_by: UserId
│
├── Memberships (Collection)
│   └── ProjectMembership
│       ├── user_id: UserId
│       ├── role: Enum(owner, admin, member, viewer)
│       └── invited_at: DateTime
│
└── Repositories (Collection)
    └── Repository
```

**Invariant**: A project must have at least one owner.
**Invariant**: Repository URLs must be unique within a project.

### Aggregate: Repository

```
Repository
├── id: UUID
├── project_id: UUID
├── git_url: URL
├── git_branch: String
├── local_path: Path
├── status: Enum(cloning, indexed, error)
├── file_count: Integer
├── total_bytes: Integer
│
├── IndexedFiles (Collection)
│   └── IndexedFile
│       ├── path: Path
│       ├── language: String
│       ├── hash: SHA256
│       ├── nodes: JSON (AST summary)
│       └── last_indexed: DateTime
│
└── CodeChunks (Collection)
    └── CodeChunk
```

**Invariant**: Repository must be indexed before analysis.
**Invariant**: File hash checked to skip re-indexing unchanged files.

### Aggregate: Analysis

```
Analysis
├── id: UUID
├── project_id: UUID
├── repository_id: UUID
├── title: String
├── error_context: ErrorContext (VO)
├── status: Enum(queued, indexing, analyzing, rca, patching, validating, completed, failed)
├── created_at: DateTime
├── completed_at: DateTime?
│
├── AnalysisRun (collection)
│   └── AnalysisRun
│       ├── id: UUID
│       ├── step: String
│       ├── status: Enum(running, completed, failed)
│       ├── started_at: DateTime
│       ├── completed_at: DateTime?
│       ├── input: JSON
│       ├── output: JSON
│       └── error: Text?
│
├── BugLocalizationResult
│   └── SuspiciousFile (collection)
│       ├── file_path: Path
│       ├── suspicion_score: Float
│       ├── matched_lines: Integer[]
│       └── evidence: Text
│
├── RootCauseResult
│   ├── summary: Text
│   ├── root_file: Path
│   ├── root_line: Integer
│   ├── cause_chain: Text
│   ├── evidence_chunks: CodeChunkId[]
│   └── confidence: Float
│
├── PatchResult? (V1)
│   └── Patch
│       ├── diff: Text
│       ├── validation_score: Float
│       ├── tests_passed: Integer
│       ├── tests_failed: Integer
│       ├── lint_errors: Integer
│       └── type_errors: Integer
│
└── Report
    ├── markdown: Text
    └── format: Enum(markdown, pdf, html)
```

**Invariant**: Analysis can only transition through valid status states.
**Invariant**: BugLocalization must complete before RCA.

## Value Objects

```python
# Value Objects (immutable, no identity)

@dataclass(frozen=True)
class ErrorContext:
    stacktrace: str | None
    logs: str | None
    error_message: str | None
    description: str | None
    environment: str | None
    steps_to_reproduce: str | None

@dataclass(frozen=True)
class SuspicionScore:
    value: float  # 0.0 - 1.0

@dataclass(frozen=True)
class CodeLocation:
    file_path: str
    start_line: int
    end_line: int

@dataclass(frozen=True)
class DiffPatch:
    diff_text: str
    modified_files: list[str]

@dataclass(frozen=True)
class EmbeddingVector:
    vector: list[float]
    model: str
    dimensions: int

@dataclass(frozen=True)
class ConfidenceScore:
    value: float  # 0.0 - 1.0
    model_used: str
    reasoning: str

@dataclass(frozen=True)
class AnalysisStatus:
    value: str  # Enum of valid statuses
```

## Domain Events

| Event | Publisher | Subscribers | Payload |
|---|---|---|---|
| `AnalysisSubmitted` | API | Orchestrator | analysis_id, repo_id, error_context |
| `RepositoryIndexed` | Indexer Agent | Analysis | repo_id, chunk_count |
| `EmbeddingsGenerated` | Embedding Agent | Vector Store | chunk_ids, vector_ids |
| `BugLocalizationCompleted` | Bug Localizer | RCA Agent | analysis_id, suspicious_files |
| `RootCauseCompleted` | RCA Agent | Report Gen | analysis_id, rca_result |
| `PatchGenerated` | Patch Generator | Validator | analysis_id, patch_id |
| `ValidationCompleted` | Validator | Report Gen | analysis_id, validation_score |
| `AnalysisCompleted` | Report Gen | API/WebSocket | analysis_id, report_url |
| `AnalysisFailed` | Orchestrator | API/WebSocket | analysis_id, error_msg |

## Domain Services

| Service | Context | Responsibility |
|---|---|---|
| `RepositoryIndexingService` | Analysis | Clone repo, walk files, invoke Indexer agent |
| `ChunkingService` | Analysis | Split files into semantic chunks via tree-sitter |
| `EmbeddingService` | Analysis | Generate embeddings via Ollama, store in pgvector |
| `SearchService` | Analysis | Hybrid search (vector + FTS), reranking |
| `BugLocalizationService` | Analysis | Correlate error context with code chunks |
| `RootCauseService` | Analysis | LLM-driven causal analysis |
| `PatchService` | Analysis | Generate candidate patches |
| `SandboxService` | Sandbox | Manage Podman containers for testing |
| `ValidationService` | Analysis | Run tests, lint, type-check in sandbox |
| `ReportingService` | Analysis | Compile final report |
| `GitService` | Repository | Clone, pull, list branches, get diffs |
