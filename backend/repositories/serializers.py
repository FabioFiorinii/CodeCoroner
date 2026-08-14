import re
from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import Repository, IndexedFile, CodeChunk, ChunkEmbedding


GIT_URL_PATTERN = re.compile(
    r'^(https?://|git@)[\w\.-]+(:[\d]+)?[/:][\w\.-]+/[\w\.-]+(\.git)?/?$'
)


class RepositoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ['id', 'git_url', 'git_branch']
        read_only_fields = ['id']

    def validate_git_url(self, value):
        if not GIT_URL_PATTERN.match(value):
            raise serializers.ValidationError('Invalid git URL format.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        repo = super().create(validated_data)
        repo.groups.set(request.user.groups.all())
        return repo


class RepositorySerializer(serializers.ModelSerializer):
    assigned_projects = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='id',
    )
    groups = serializers.SlugRelatedField(
        many=True, slug_field='name', read_only=True,
    )

    class Meta:
        model = Repository
        fields = [
            'id', 'git_url', 'git_branch', 'auto_pull',
            'status', 'file_count', 'total_bytes', 'error_message', 'last_indexed_at',
            'assigned_projects', 'groups', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'file_count', 'total_bytes', 'error_message', 'last_indexed_at', 'assigned_projects', 'groups', 'created_at', 'updated_at']

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
