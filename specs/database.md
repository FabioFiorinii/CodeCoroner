# CodeCoroner — Database Design

## ER Diagram (Textual)

```
┌────────────────┐       ┌──────────────────┐       ┌────────────────────┐
│    users        │       │    projects       │       │   project_members  │
│────────────────│       │──────────────────│       │────────────────────│
│ id (PK, UUID)  │──1:N──│ id (PK, UUID)    │──1:N──│ id (PK, UUID)      │
│ email          │       │ name             │       │ project_id (FK)    │
│ username       │       │ description      │       │ user_id (FK)       │
│ password_hash  │       │ created_by (FK)  │       │ role: varchar      │
│ is_active      │       │ created_at       │       │ created_at         │
│ is_superuser   │       │ updated_at       │       └────────────────────┘
│ created_at     │       └──────────────────┘
└────────────────┘               │
        │                        │
        │                        │ 1:N
        │ 1:N                    ▼
        │               ┌────────────────────┐
        │               │   repositories      │
        │               │────────────────────│
        │               │ id (PK, UUID)      │
        │               │ project_id (FK)    │
        │               │ git_url            │
        │               │ git_branch         │
        │               │ local_path         │
        │               │ status: varchar    │
        │               │ file_count         │
        │               │ total_bytes        │
        │               │ last_indexed_at    │
        │               │ created_at         │
        │               │ updated_at         │
        │               └────────┬───────────┘
        │                        │
        │                        │ 1:N
        │                        ▼
        │               ┌────────────────────┐       ┌────────────────────┐
        │               │  indexed_files     │       │   code_chunks      │
        │               │────────────────────│       │────────────────────│
        │               │ id (PK, UUID)      │──1:N──│ id (PK, UUID)      │
        │               │ repository_id (FK) │       │ file_id (FK)       │
        │               │ file_path          │       │ chunk_type: varchar│
        │               │ language           │       │ start_line         │
        │               │ file_hash          │       │ end_line           │
        │               │ ast_nodes (JSONB)  │       │ content: text      │
        │               │ last_indexed_at    │       │ tokens_count       │
        │               │ created_at         │       │ embedding vector(?)│
        │               └────────────────────┘       │ parent_chunk_id    │
        │                                             │ metadata (JSONB)   │
        │ 1:N                                         │ created_at         │
        │               ┌────────────────────┐        └─────────┬──────────┘
        │               │   analyses          │                  │
        │               │────────────────────│                  │ 1:1 (optional)
        │               │ id (PK, UUID)      │                  │
        ├──────────────N│ user_id (FK)       │                  ▼
        │               │ project_id (FK)    │       ┌────────────────────┐
        │               │ repository_id (FK) │       │ chunk_embeddings   │
        │               │ title: varchar     │       │────────────────────│
        │               │ error_context(JSONB)│      │ id (PK, UUID)      │
        │               │ status: varchar    │       │ chunk_id (FK, UQ)  │
        │               │ created_at         │       │ embedding vector   │
        │               │ completed_at       │       │ model: varchar     │
        │               │ duration_seconds   │       │ dimensions: int    │
        │               │ error_message      │       │ created_at         │
        │               └────────┬───────────┘       └────────────────────┘
        │                        │
        │                        │ 1:N
        │                        ▼
        │               ┌────────────────────┐       ┌────────────────────┐
        │               │  analysis_runs      │       │  bug_localization  │
        │               │────────────────────│       │────────────────────│
        │               │ id (PK, UUID)      │──1:1──│ id (PK, UUID)      │
        │               │ analysis_id (FK)   │       │ analysis_id (FK,UQ)│
        │               │ step: varchar      │       │ summary: text      │
        │               │ status: varchar    │       │ created_at         │
        │               │ input (JSONB)      │       └────────┬───────────┘
        │               │ output (JSONB)     │               │
        │               │ started_at         │               │ 1:N
        │               │ completed_at       │               ▼
        │               │ error: text        │       ┌────────────────────┐
        │               └────────────────────┘       │  susp_file_scores   │
        │                                             │────────────────────│
        │                                             │ id (PK, UUID)      │
        │                                             │ localization_id(FK)│
        │                                             │ file_path          │
        │                                             │ suspicion_score    │
        │                                             │ matched_lines(INT[])│
        │                                             │ evidence: text     │
        │                                             │ rank: int          │
        │                                             └────────────────────┘
        │                        │
        │                        │ 1:1 (optional)
        │                        ▼
        │               ┌────────────────────┐
        │               │  root_causes        │
        │               │────────────────────│
        │               │ id (PK, UUID)      │
        │               │ analysis_id (FK,UQ) │
        │               │ summary: text       │
        │               │ root_file: varchar  │
        │               │ root_line: int      │
        │               │ cause_chain: text   │
        │               │ confidence: float   │
        │               │ reasoning: text     │
        │               │ created_at          │
        │               └────────────────────┘
        │                        │
        │                        │ 1:1 (optional, V1)
        │                        ▼
        │               ┌────────────────────┐
        │               │   patches           │
        │               │────────────────────│
        │               │ id (PK, UUID)      │
        │               │ analysis_id (FK,UQ) │
        │               │ diff: text          │
        │               │ summary: text       │
        │               │ status: varchar     │
        │               │ created_at          │
        │               └────────────────────┘
        │                        │
        │                        │ 1:1 (V1)
        │                        ▼
        │               ┌────────────────────┐
        │               │ patch_validations   │
        │               │────────────────────│
        │               │ id (PK, UUID)      │
        │               │ patch_id (FK,UQ)   │
        │               │ tests_passed        │
        │               │ tests_failed        │
        │               │ tests_skipped       │
        │               │ lint_errors         │
        │               │ lint_warnings       │
        │               │ type_errors         │
        │               │ overall_score: float│
        │               │ output_log: text    │
        │               │ created_at          │
        │               └────────────────────┘
        │                        │
        │                        │ 1:1
        │                        ▼
        │               ┌────────────────────┐
        │               │   reports           │
        │               │────────────────────│
        │               │ id (PK, UUID)      │
        │               │ analysis_id (FK,UQ) │
        │               │ markdown: text      │
        │               │ format: varchar     │
        │               │ created_at          │
        │               └────────────────────┘
```

## SQL Schema — Core Tables

```sql
-- Extension: Enable UUID, vector, and full-text search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================
-- USERS & AUTH
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(254) UNIQUE NOT NULL,
    username VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE api_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    scopes JSONB DEFAULT '[]',
    expires_at TIMESTAMPTZ,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PROJECTS
-- ============================================

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE project_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

-- ============================================
-- REPOSITORIES & CODE
-- ============================================

CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    git_url TEXT NOT NULL,
    git_branch VARCHAR(255) DEFAULT 'main',
    local_path TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'cloning', 'indexing', 'indexed', 'error')),
    file_count INTEGER DEFAULT 0,
    total_bytes BIGINT DEFAULT 0,
    last_indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_repositories_project ON repositories(project_id);

CREATE TABLE indexed_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    ast_nodes JSONB DEFAULT '{}',
    last_indexed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(repository_id, file_path)
);

CREATE INDEX idx_indexed_files_repo ON indexed_files(repository_id);
CREATE INDEX idx_indexed_files_language ON indexed_files(language);
CREATE INDEX idx_indexed_files_hash ON indexed_files(file_hash);

-- ============================================
-- CODE CHUNKS & EMBEDDINGS
-- ============================================

CREATE TABLE code_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES indexed_files(id) ON DELETE CASCADE,
    chunk_type VARCHAR(50) NOT NULL CHECK (chunk_type IN (
        'function', 'class', 'method', 'block', 'module', 'comment', 'docstring'
    )),
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content TEXT NOT NULL,
    tokens_count INTEGER DEFAULT 0,
    parent_chunk_id UUID REFERENCES code_chunks(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_code_chunks_file ON code_chunks(file_id);
CREATE INDEX idx_code_chunks_type ON code_chunks(chunk_type);
CREATE INDEX idx_code_chunks_parent ON code_chunks(parent_chunk_id);

-- Full-text search on chunk content
CREATE INDEX idx_code_chunks_fts ON code_chunks USING gin(to_tsvector('english', content));

-- Trigram index for fuzzy matching
CREATE INDEX idx_code_chunks_trgm ON code_chunks USING gin(content gin_trgm_ops);

-- Embeddings stored in a dedicated table for pgvector
CREATE TABLE chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID UNIQUE NOT NULL REFERENCES code_chunks(id) ON DELETE CASCADE,
    embedding vector(768) NOT NULL,  -- nomic-embed-text: 768 dimensions
    model VARCHAR(100) NOT NULL DEFAULT 'nomic-embed-text',
    dimensions INTEGER NOT NULL DEFAULT 768,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for approximate nearest neighbor search
CREATE INDEX idx_chunk_embeddings_ivfflat
    ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- HNSW index for better recall (use if pgvector ≥ 0.5)
-- CREATE INDEX idx_chunk_embeddings_hnsw
--     ON chunk_embeddings USING hnsw (embedding vector_cosine_ops)
--     WITH (m = 16, ef_construction = 200);

-- ============================================
-- ANALYSES
-- ============================================

CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    repository_id UUID NOT NULL REFERENCES repositories(id),
    title VARCHAR(255),
    error_context JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'queued'
        CHECK (status IN (
            'queued', 'indexing', 'analyzing',
            'bug_localization', 'rca', 'patching',
            'validating', 'completed', 'failed'
        )),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    error_message TEXT
);

CREATE INDEX idx_analyses_user ON analyses(user_id);
CREATE INDEX idx_analyses_project ON analyses(project_id);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_created ON analyses(created_at DESC);

CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    step VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'skipped')),
    input JSONB,
    output JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error TEXT
);

CREATE INDEX idx_analysis_runs_parent ON analysis_runs(analysis_id);

-- ============================================
-- BUG LOCALIZATION RESULTS
-- ============================================

CREATE TABLE bug_localizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID UNIQUE NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE susp_file_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    localization_id UUID NOT NULL REFERENCES bug_localizations(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    suspicion_score FLOAT NOT NULL,
    matched_lines INTEGER[] DEFAULT '{}',
    evidence TEXT,
    rank INTEGER NOT NULL
);

CREATE INDEX idx_susp_file_localization ON susp_file_scores(localization_id);
CREATE INDEX idx_susp_file_score ON susp_file_scores(suspicion_score DESC);

-- ============================================
-- ROOT CAUSE ANALYSIS
-- ============================================

CREATE TABLE root_causes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID UNIQUE NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    root_file VARCHAR(1024) NOT NULL,
    root_line INTEGER,
    cause_chain TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    reasoning TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PATCHES & VALIDATION (V1)
-- ============================================

CREATE TABLE patches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID UNIQUE NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    diff TEXT NOT NULL,
    summary TEXT,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'applied', 'validated', 'rejected', 'error')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE patch_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patch_id UUID UNIQUE NOT NULL REFERENCES patches(id) ON DELETE CASCADE,
    tests_passed INTEGER DEFAULT 0,
    tests_failed INTEGER DEFAULT 0,
    tests_skipped INTEGER DEFAULT 0,
    lint_errors INTEGER DEFAULT 0,
    lint_warnings INTEGER DEFAULT 0,
    type_errors INTEGER DEFAULT 0,
    overall_score FLOAT DEFAULT 0.0,
    output_log TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- REPORTS
-- ============================================

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID UNIQUE NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    markdown TEXT NOT NULL,
    format VARCHAR(10) DEFAULT 'markdown'
        CHECK (format IN ('markdown', 'pdf', 'html')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- EVENTS (Audit Log)
-- ============================================

CREATE TABLE domain_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_domain_events_aggregate ON domain_events(aggregate_type, aggregate_id);
CREATE INDEX idx_domain_events_type ON domain_events(event_type);
CREATE INDEX idx_domain_events_created ON domain_events(created_at DESC);

-- ============================================
-- WEBHOOKS
-- ============================================

CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    secret VARCHAR(255),
    events VARCHAR(50)[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MATERIALIZED VIEWS
-- ============================================

-- Per-project analysis stats
CREATE MATERIALIZED VIEW mv_project_stats AS
SELECT
    p.id AS project_id,
    p.name AS project_name,
    COUNT(DISTINCT a.id) AS total_analyses,
    COUNT(DISTINCT r.id) AS total_repositories,
    AVG(a.duration_seconds) AS avg_duration_seconds,
    COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) AS completed_analyses,
    COUNT(DISTINCT CASE WHEN a.status = 'failed' THEN a.id END) AS failed_analyses
FROM projects p
LEFT JOIN analyses a ON a.project_id = p.id
LEFT JOIN repositories r ON r.project_id = p.id
GROUP BY p.id, p.name;
```

## Vector Search Indexes

```sql
-- Primary: Cosine similarity on code chunk embeddings
CREATE INDEX idx_embeddings_cosine
    ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- For hybrid search: composite query
-- SELECT c.id, c.content, c.file_id,
--        1 - (ce.embedding <=> query_embedding) AS cosine_sim,
--        ts_rank(to_tsvector('english', c.content), query_tsquery) AS text_rank
-- FROM code_chunks c
-- JOIN chunk_embeddings ce ON ce.chunk_id = c.id
-- WHERE
--     -- Semantic filter
--     1 - (ce.embedding <=> query_embedding) > 0.6
--     OR
--     -- Keyword filter (for hybrid)
--     to_tsvector('english', c.content) @@ query_tsquery
-- ORDER BY
--     (0.7 * (1 - (ce.embedding <=> query_embedding)) +
--      0.3 * ts_rank(to_tsvector('english', c.content), query_tsquery)) DESC
-- LIMIT 20;
```

## Django Model Mapping

```
PostgreSQL Table           → Django Model
──────────────────────────────────────────────────
users                     → User (AbstractUser)
api_tokens                → ApiToken
projects                  → Project
project_members           → ProjectMembership
repositories              → Repository
indexed_files             → IndexedFile
code_chunks               → CodeChunk
chunk_embeddings          → ChunkEmbedding
analyses                  → Analysis
analysis_runs             → AnalysisRun
bug_localizations         → BugLocalization
susp_file_scores          → SuspiciousFileScore
root_causes               → RootCause
patches                   → Patch
patch_validations         → PatchValidation
reports                   → Report
domain_events             → DomainEvent
webhooks                  → Webhook
```
