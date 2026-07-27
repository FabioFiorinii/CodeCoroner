# CodeCoroner Design Document

## Step 3: Repository Indexing Pipeline

### 3.1 Data Model

- **Repository**: Tracks git repos with status (pending/cloning/indexing/indexed/error), file count, byte count, error messages, and timestamps. UUID primary key. Ordered by `-created_at`.
- **IndexedFile**: Represents a single indexed file with its path, detected language, file hash (for change detection), and stored AST nodes.
- **CodeChunk**: Semantic units extracted from files (module, class, function, method, block, docstring). Points to parent chunk for hierarchy. Stores content, line ranges, token count, and metadata.
- **ChunkEmbedding**: One-to-one with CodeChunk, stores pgvector embedding (768d, nomic-embed-text model).

### 3.2 API Design

- **RepositoryViewSet** (`/api/v1/repositories/`):
  - Standard CRUD with `IsProjectMember` permission (project-scoped isolation)
  - `RepositoryCreateSerializer` for POST (validates git URL via regex, project membership)
  - `RepositorySerializer` for GET/PATCH (includes `project_name`, read-only status fields)
  - `POST /{id}/index/` - trigger indexing (409 if already cloning/indexing)
  - `POST /{id}/reindex/` - clear files + chunks, reset status, re-clone
  - `GET /{id}/status/` - lightweight status object (for polling)
  - `GET /{id}/files/` - paginated indexed files
  - `GET /{id}/chunks/` - paginated code chunks (with `has_embedding` flag)

### 3.3 Tasks & Processing

- **clone_repository_task**: Clones/pulls repo via GitService, then enqueues `index_repository_task`. Error → sets status=error with message.
- **index_repository_task**: Walks local repo, detects file types, parses with tree-sitter, generates CodeChunks via SemanticChunker, saves IndexedFiles.
- **SemanticChunker**: Language-agnostic chunker wrapping tree-sitter parsers (Python, TypeScript, JavaScript, Go, Rust, Java). Falls back to line-based splitting for unsupported languages.

### 3.4 Embedding Pipeline (ai-engine)

- **FastAPI server** at port 8002 with `/health`, `/embed`, `/index` endpoints.
- **RepositoryIndexer**: Reads code chunks from Django DB via psycopg2, indexes with tree-sitter, calls Ollama embeddings.
- **EmbeddingGenerator**: Batches chunk texts (batch_size from settings), sends to Ollama `/api/embeddings`, handles partial failures, stores in ChunkEmbedding table.
- **OllamaClient**: Uses `prompt` field (not `input`) for `/api/embeddings` on nomic-embed-text.

### 3.5 Testing

- 27 repository tests covering:
  - CRUD operations (create, list, retrieve, update, delete)
  - Input validation (git URL regex, project membership)
  - Auth enforcement (unauthenticated, non-member)
  - Custom actions (index, reindex with conflict handling)
  - Data access isolation (non-member gets 404)
  - Task execution (clone success/failure, indexing, chunking)
- 45 total backend tests across accounts, projects, and repositories.
- Custom `PgVectorTestRunner` for pgvector-compatible test database creation.

### 3.6 Frontend

- **RepositoryListPage** (`/projects/:projectId/repos`): Grid of repo cards with status badges, search filter, loading/empty/error states.
- **RepositoryNewPage** (`/projects/:projectId/repos/new`): Git URL + branch form with validation.
- **RepositoryDetailPage** (`/projects/:projectId/repos/:repoId`): Status card with auto-refresh (3s polling during active indexing), file list, collapsible chunk browser, Index/Reindex/Delete actions.
- **ProjectDetailPage** updated with link to repository list.
- React Query hooks for all repository endpoints with cache invalidation.
