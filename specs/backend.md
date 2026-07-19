# CodeCoroner — Backend Design

## Django Apps Structure

```
backend/
├── config/                  # Django project config
│   ├── settings/
│   │   ├── base.py         # Shared settings
│   │   ├── dev.py          # Development overrides
│   │   ├── prod.py         # Production overrides
│   │   └── test.py         # Test settings
│   ├── urls.py              # Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                # User & auth app
├── projects/                # Project management app
├── repositories/            # Repository management app
├── analyses/                # Analysis orchestration app
├── agents/                  # AI agent communication app
├── reports/                 # Report generation app
├── webhooks/                # Webhook integrations app
├── common/                  # Shared utilities, abstract models
└── core/                    # Domain events, base services
```

## App: accounts

```python
# Models
class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid4)
    email = EmailField(unique=True)
    api_rate_limit = IntegerField(default=100)  # requests/hour

class ApiToken(models.Model):
    user = ForeignKey(User, CASCADE)
    name = CharField(max_length=100)
    token_hash = CharField(max_length=255)
    scopes = JSONField(default=list)
    expires_at = DateTimeField(null=True)
    is_revoked = BooleanField(default=False)

# Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'is_active', 'created_at']

class RegisterSerializer(serializers.Serializer):
    email = EmailField()
    username = CharField()
    password = CharField(write_only=True)

# Views
class RegisterView(CreateAPIView): ...
class LoginView(ObtainAuthToken): ...
class UserDetailView(RetrieveUpdateAPIView): ...

# URLs: /api/v1/auth/register, /api/v1/auth/login, /api/v1/auth/me
```

## App: projects

```python
# Models
class Project(models.Model):
    id = UUIDField(primary_key=True, default=uuid4)
    name = CharField(max_length=255)
    description = TextField(blank=True)
    created_by = ForeignKey(User, CASCADE, related_name='owned_projects')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner'
        ADMIN = 'admin'
        MEMBER = 'member'
        VIEWER = 'viewer'

    project = ForeignKey(Project, CASCADE, related_name='memberships')
    user = ForeignKey(User, CASCADE, related_name='memberships')
    role = CharField(max_length=20, choices=Role.choices)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

# Services
class ProjectService:
    @staticmethod
    def create_project(name, description, user) -> Project: ...
    @staticmethod
    def add_member(project, user, role) -> ProjectMembership: ...
    @staticmethod
    def remove_member(project, user) -> None: ...

# Viewsets
class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectPermission]

    def get_queryset(self):
        return Project.objects.filter(
            Q(created_by=self.request.user) |
            Q(memberships__user=self.request.user)
        ).distinct()

# URLs: /api/v1/projects/{id}/members/
```

## App: repositories

```python
# Models
class Repository(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        CLONING = 'cloning'
        INDEXING = 'indexing'
        INDEXED = 'indexed'
        ERROR = 'error'

    project = ForeignKey(Project, CASCADE, related_name='repositories')
    git_url = CharField(max_length=2048)
    git_branch = CharField(max_length=255, default='main')
    local_path = CharField(max_length=1024, null=True)
    status = CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    file_count = IntegerField(default=0)
    total_bytes = BigIntegerField(default=0)
    last_indexed_at = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class IndexedFile(models.Model):
    repository = ForeignKey(Repository, CASCADE, related_name='indexed_files')
    file_path = CharField(max_length=2048)
    language = CharField(max_length=50)
    file_hash = CharField(max_length=64)  # SHA-256
    ast_nodes = JSONField(default=dict)
    last_indexed_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('repository', 'file_path')

# Services
class GitService:
    def clone_or_pull(self, repo: Repository) -> Path:
        """Clone if absent, pull if exists. Returns local path."""

    def get_file_tree(self, repo_path: Path) -> list[dict]:
        """Walk directory, return file list with sizes and hashes."""

    def get_diff(self, repo: Repository, commit_a: str, commit_b: str) -> str: ...

class RepositoryService:
    def __init__(self, git_service: GitService, indexer_agent: RepositoryIndexer):
        ...

    def index_repository(self, repo_id: UUID) -> None:
        """Orchestrate cloning + indexing + chunking + embedding."""

# Viewsets
class RepositoryViewSet(ModelViewSet):
    @action(detail=True, methods=['post'])
    def index(self, request, pk=None):
        """Trigger async indexing via Celery."""

    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """List indexed files."""

    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """List code chunks (paginated)."""
```

## App: analyses

```python
# Models
class Analysis(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued'
        INDEXING = 'indexing'
        ANALYZING = 'analyzing'
        BUG_LOCALIZATION = 'bug_localization'
        RCA = 'rca'
        PATCHING = 'patching'
        VALIDATING = 'validating'
        COMPLETED = 'completed'
        FAILED = 'failed'

    user = ForeignKey(User, CASCADE, related_name='analyses')
    project = ForeignKey(Project, CASCADE, related_name='analyses')
    repository = ForeignKey(Repository, CASCADE, related_name='analyses')
    title = CharField(max_length=255, blank=True)
    error_context = JSONField(default=dict)
    status = CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True)
    duration_seconds = IntegerField(null=True)
    error_message = TextField(blank=True)

class AnalysisRun(models.Model):
    analysis = ForeignKey(Analysis, CASCADE, related_name='runs')
    step = CharField(max_length=50)
    status = CharField(max_length=20, choices=RunStatus.choices, default='running')
    input = JSONField(default=dict)
    output = JSONField(default=dict)
    started_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True)
    error = TextField(blank=True)

# USE CASE: SubmitAnalysis
class SubmitAnalysisUseCase:
    def __init__(self, analysis_repo, orchestrator):
        ...

    def execute(self, user_id, project_id, repository_id, error_context) -> Analysis:
        """Create analysis, validate, enqueue pipeline."""

# USE CASE: GetAnalysisStatus
class GetAnalysisStatusUseCase:
    def execute(self, analysis_id, user_id) -> AnalysisStatusDTO: ...

# USE CASE: ListAnalyses
class ListAnalysesUseCase:
    def execute(self, user_id, project_id, filters) -> Page[AnalysisSummaryDTO]: ...

# API
class AnalysisViewSet(ModelViewSet):
    serializer_class = AnalysisSerializer

    def perform_create(self, serializer):
        analysis = serializer.save(user=self.request.user)
        # Enqueue Celery task
        run_analysis_pipeline.delay(str(analysis.id))

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Return current status + step details."""

    @action(detail=True, methods=['get'])
    def localization(self, request, pk=None):
        """Return bug localization results."""

    @action(detail=True, methods=['get'])
    def root_cause(self, request, pk=None):
        """Return RCA results."""

    @action(detail=True, methods=['get'])
    def patch(self, request, pk=None):
        """Return generated patch (V1)."""

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Return final report."""

# URLs: /api/v1/analyses/{id}/localization/
#        /api/v1/analyses/{id}/root-cause/
#        /api/v1/analyses/{id}/patch/
#        /api/v1/analyses/{id}/report/
```

## Celery Tasks

```python
# tasks/analysis_tasks.py

@shared_task(bind=True, max_retries=3)
def run_analysis_pipeline(self, analysis_id: str):
    """Main pipeline orchestrator."""
    analysis = Analysis.objects.get(id=analysis_id)
    orchestrator = AnalysisOrchestrator()
    try:
        orchestrator.execute(analysis)
    except Exception as e:
        analysis.status = Analysis.Status.FAILED
        analysis.error_message = str(e)
        analysis.save(update_fields=['status', 'error_message'])
        raise

@shared_task
def index_repository_task(repo_id: str): ...
@shared_task
def generate_embeddings_task(chunk_ids: list[str]): ...
@shared_task
def bug_localization_task(analysis_id: str): ...
@shared_task
def root_cause_task(analysis_id: str): ...
@shared_task
def generate_patch_task(analysis_id: str): ...
@shared_task
def validate_patch_task(patch_id: str): ...
@shared_task
def generate_report_task(analysis_id: str): ...
```

## Analysis Orchestrator

```python
class AnalysisOrchestrator:
    """State machine for the analysis pipeline."""

    def execute(self, analysis: Analysis) -> None:
        self._update_status(analysis, Analysis.Status.INDEXING)
        self._step_ensure_repo_indexed(analysis)

        self._update_status(analysis, Analysis.Status.ANALYZING)
        self._step_analyze_input(analysis)

        self._update_status(analysis, Analysis.Status.BUG_LOCALIZATION)
        self._step_bug_localization(analysis)

        self._update_status(analysis, Analysis.Status.RCA)
        self._step_root_cause(analysis)

        # V1 only:
        # self._step_generate_patch(analysis)
        # self._step_validate_patch(analysis)

        self._update_status(analysis, Analysis.Status.COMPLETED)

    def _step_ensure_repo_indexed(self, analysis):
        if analysis.repository.status != Repository.Status.INDEXED:
            index_repository_task(str(analysis.repository_id))

    def _step_analyze_input(self, analysis):
        agent = LogAnalyzerAgent()
        result = agent.analyze(analysis.error_context)
        self._record_run(analysis, 'analyze_input', result)

    def _step_bug_localization(self, analysis):
        agent = BugLocalizerAgent()
        result = agent.localize(
            repo_id=analysis.repository_id,
            error_context=analysis.error_context
        )
        BugLocalization.objects.create(
            analysis=analysis,
            summary=result['summary']
        )
        for rank, file in enumerate(result['suspicious_files'], 1):
            SuspiciousFileScore.objects.create(
                analysis=analysis,
                file_path=file['path'],
                suspicion_score=file['score'],
                matched_lines=file.get('lines', []),
                evidence=file.get('evidence', ''),
                rank=rank
            )

    def _step_root_cause(self, analysis):
        agent = RootCauseAgent()
        result = agent.analyze(
            repo_id=analysis.repository_id,
            error_context=analysis.error_context,
            suspicious_files=SuspiciousFileScore.objects
                .filter(analysis=analysis)
                .order_by('rank')
        )
        RootCause.objects.create(
            analysis=analysis,
            summary=result['summary'],
            root_file=result['root_file'],
            root_line=result.get('root_line'),
            cause_chain=result['cause_chain'],
            confidence=result.get('confidence', 0.0),
            reasoning=result['reasoning']
        )
```

## API Reference (MVP)

```
METHOD  ENDPOINT                          DESCRIPTION
──────  ────────────────────────────────  ──────────────────────────
POST    /api/v1/auth/register             Register new user
POST    /api/v1/auth/login                Login, returns JWT
GET     /api/v1/auth/me                   Get current user

GET     /api/v1/projects                  List projects
POST    /api/v1/projects                  Create project
GET     /api/v1/projects/{id}             Get project detail
PUT     /api/v1/projects/{id}             Update project
DELETE  /api/v1/projects/{id}             Delete project
GET     /api/v1/projects/{id}/members     List members
POST    /api/v1/projects/{id}/members     Add member

GET     /api/v1/repositories              List repos
POST    /api/v1/repositories              Add repo (git URL)
GET     /api/v1/repositories/{id}         Get repo detail
POST    /api/v1/repositories/{id}/index   Trigger indexing
GET     /api/v1/repositories/{id}/files   List indexed files
GET     /api/v1/repositories/{id}/chunks  List code chunks

POST    /api/v1/analyses                  Submit analysis
GET     /api/v1/analyses                  List analyses
GET     /api/v1/analyses/{id}             Get analysis
GET     /api/v1/analyses/{id}/status      Get status (poll)
GET     /api/v1/analyses/{id}/localization  Get bug localization
GET     /api/v1/analyses/{id}/root-cause  Get root cause
GET     /api/v1/analyses/{id}/patch       Get patch (V1)
GET     /api/v1/analyses/{id}/report      Get report

GET     /api/v1/ws/analyses/{id}          WebSocket status stream
```

## Authentication & Authorization

```python
# JWT via djangorestframework-simplejwt
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardPagination',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/hour',
        'anon': '10/hour',
    }
}

# Custom permission
class ProjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'project'):
            project = obj.project
        else:
            project = obj
        return project.memberships.filter(
            user=request.user,
            role__in=['owner', 'admin', 'member']
        ).exists()
```

## Key Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "django>=5.1,<6.0",
    "djangorestframework>=3.15",
    "djangorestframework-simplejwt>=5.3",
    "django-filter>=24.1",
    "django-cors-headers>=4.3",
    "psycopg2-binary>=2.9",
    "django-pgvector>=0.3",
    "celery>=5.4",
    "redis>=5.0",
    "channels>=4.1",           # WebSocket
    "daphne>=4.1",             # ASGI server
    "gunicorn>=22.0",
    "pydantic>=2.7",           # Data validation
    "pydantic-settings>=2.2",
    "httpx>=0.27",             # HTTP client for Ollama
    "structlog>=24.1",         # Structured logging
    "sentry-sdk>=2.5",        # Error tracking
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-django>=4.8",
    "pytest-cov>=5.0",
    "factory-boy>=3.3",
    "ruff>=0.5",
    "mypy>=1.10",
    "django-stubs>=5.0",
    "ipdb",
]
```
