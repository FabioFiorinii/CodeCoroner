from rest_framework import serializers
from .models import Repository, IndexedFile, CodeChunk, ChunkEmbedding

class RepositorySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Repository
        fields = [
            'id', 'project', 'project_name', 'git_url', 'git_branch',
            'status', 'file_count', 'total_bytes', 'last_indexed_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'file_count', 'total_bytes', 'last_indexed_at', 'created_at', 'updated_at']

class IndexedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexedFile
        fields = ['id', 'file_path', 'language', 'file_hash', 'last_indexed_at']
        read_only_fields = ['id', 'last_indexed_at']

class CodeChunkSerializer(serializers.ModelSerializer):
    file_path = serializers.CharField(source='file.file_path', read_only=True)
    has_embedding = serializers.SerializerMethodField()

    class Meta:
        model = CodeChunk
        fields = [
            'id', 'file', 'file_path', 'chunk_type', 'start_line', 'end_line',
            'content', 'tokens_count', 'parent_chunk', 'metadata', 'has_embedding',
        ]
        read_only_fields = ['id', 'has_embedding']

    def get_has_embedding(self, obj):
        return hasattr(obj, 'embedding')
