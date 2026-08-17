import uuid

from django.db import models
from pgvector.django import VectorField


class Repository(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        CLONING = 'cloning'
        INDEXING = 'indexing'
        INDEXED = 'indexed'
        ERROR = 'error'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='repositories',
        null=True,
        blank=True,
    )
    assigned_projects = models.ManyToManyField(
        'projects.Project',
        related_name='assigned_repositories',
        blank=True,
    )
    groups = models.ManyToManyField('auth.Group', related_name='repositories', blank=True)
    git_url = models.CharField(max_length=2048)
    git_branch = models.CharField(max_length=255, default='main')
    auto_pull = models.BooleanField(default=False)
    local_path = models.CharField(max_length=1024, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    file_count = models.IntegerField(default=0)
    total_bytes = models.BigIntegerField(default=0)
    summary = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    last_indexed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'repositories'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.git_url} ({self.status})'


class IndexedFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name='indexed_files',
    )
    file_path = models.CharField(max_length=2048)
    language = models.CharField(max_length=50)
    file_hash = models.CharField(max_length=64)
    ast_nodes = models.JSONField(default=dict)
    last_indexed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('repository', 'file_path')

    def __str__(self):
        return self.file_path


class CodeChunk(models.Model):
    class ChunkType(models.TextChoices):
        FUNCTION = 'function'
        CLASS_DEF = 'class'
        METHOD = 'method'
        BLOCK = 'block'
        MODULE = 'module'
        DOCSTRING = 'docstring'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(
        IndexedFile,
        on_delete=models.CASCADE,
        related_name='code_chunks',
    )
    chunk_type = models.CharField(max_length=50, choices=ChunkType.choices)
    start_line = models.IntegerField()
    end_line = models.IntegerField()
    content = models.TextField()
    tokens_count = models.IntegerField(default=0)
    parent_chunk = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_chunks',
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.file.file_path}:{self.start_line}-{self.end_line} ({self.chunk_type})'


class ChunkEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chunk = models.OneToOneField(
        CodeChunk,
        on_delete=models.CASCADE,
        related_name='embedding',
    )
    embedding = VectorField(dimensions=768)
    model = models.CharField(max_length=100, default='nomic-embed-text')
    dimensions = models.IntegerField(default=768)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Embedding for {self.chunk}'
