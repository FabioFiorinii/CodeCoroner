from django.contrib import admin

from .models import ChunkEmbedding, CodeChunk, IndexedFile, Repository


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ['git_url', 'project', 'status', 'file_count', 'last_indexed_at']
    search_fields = ['git_url', 'project__name']
    list_filter = ['status']


@admin.register(IndexedFile)
class IndexedFileAdmin(admin.ModelAdmin):
    list_display = ['file_path', 'language', 'repository', 'file_hash']
    search_fields = ['file_path']


@admin.register(CodeChunk)
class CodeChunkAdmin(admin.ModelAdmin):
    list_display = ['file', 'chunk_type', 'start_line', 'end_line', 'tokens_count']
    list_filter = ['chunk_type']


@admin.register(ChunkEmbedding)
class ChunkEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['chunk', 'model', 'dimensions', 'created_at']
