import uuid

from django.conf import settings
from django.db import models


class Analysis(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued'
        INDEXING = 'indexing'
        ANALYZING = 'analyzing'
        BUG_LOCALIZATION = 'bug_localization'
        RCA = 'rca'
        PATCHING = 'patching'
        VALIDATING = 'validating'
        FIX_SUGGESTION = 'fix_suggestion'
        GENERATE_REPORT = 'generate_report'
        COMPLETED = 'completed'
        FAILED = 'failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_analysis = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analyses',
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='analyses',
    )
    repository = models.ForeignKey(
        'repositories.Repository',
        on_delete=models.CASCADE,
        related_name='analyses',
    )
    repositories = models.ManyToManyField(
        'repositories.Repository',
        related_name='analysis_records',
        blank=True,
    )
    title = models.CharField(max_length=255, blank=True, default='')
    error_context = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'analyses'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.id.hex[:8]


class AnalysisRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'running'
        COMPLETED = 'completed'
        FAILED = 'failed'
        SKIPPED = 'skipped'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='runs')
    step = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    input = models.JSONField(default=dict)
    output = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, default='')

    def __str__(self):
        return f'{self.analysis.id.hex[:8]} - {self.step} ({self.status})'


class BugLocalization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.OneToOneField(
        Analysis, on_delete=models.CASCADE, related_name='bug_localization'
    )
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class SuspiciousFileScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    localization = models.ForeignKey(
        BugLocalization,
        on_delete=models.CASCADE,
        related_name='suspicious_files',
    )
    file_path = models.CharField(max_length=2048)
    suspicion_score = models.FloatField()
    matched_lines = models.JSONField(default=list)
    evidence = models.TextField(blank=True, default='')
    rank = models.IntegerField()

    class Meta:
        ordering = ['rank']


class RootCause(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, related_name='root_cause')
    summary = models.TextField()
    root_file = models.CharField(max_length=1024)
    root_line = models.IntegerField(null=True, blank=True)
    cause_chain = models.TextField()
    confidence = models.FloatField(default=0.0)
    reasoning = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Patch(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        APPLIED = 'applied'
        VALIDATED = 'validated'
        REJECTED = 'rejected'
        ERROR = 'error'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, related_name='patch')
    diff = models.TextField()
    summary = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)


class PatchValidation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patch = models.OneToOneField(Patch, on_delete=models.CASCADE, related_name='validation')
    tests_passed = models.IntegerField(default=0)
    tests_failed = models.IntegerField(default=0)
    tests_skipped = models.IntegerField(default=0)
    lint_errors = models.IntegerField(default=0)
    lint_warnings = models.IntegerField(default=0)
    type_errors = models.IntegerField(default=0)
    overall_score = models.FloatField(default=0.0)
    output_log = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)


class FixSuggestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.OneToOneField(
        Analysis, on_delete=models.CASCADE, related_name='fix_suggestion'
    )
    diff = models.TextField(blank=True, default='')
    plan = models.TextField(blank=True, default='')
    explanation = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'FixSuggestion for {self.analysis.id.hex[:8]}'


class Report(models.Model):
    class Format(models.TextChoices):
        MARKDOWN = 'markdown'
        PDF = 'pdf'
        HTML = 'html'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, related_name='report')
    markdown = models.TextField()
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.MARKDOWN)
    created_at = models.DateTimeField(auto_now_add=True)
