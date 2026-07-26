from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Repository, IndexedFile, CodeChunk
from .serializers import (
    RepositorySerializer, RepositoryCreateSerializer,
    IndexedFileSerializer, CodeChunkSerializer,
)


class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.project.memberships.filter(user=request.user).exists()


class RepositoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_serializer_class(self):
        if self.action == 'create':
            return RepositoryCreateSerializer
        return RepositorySerializer

    def get_queryset(self):
        return Repository.objects.filter(
            project__memberships__user=self.request.user
        ).select_related('project').distinct()

    def perform_create(self, serializer):
        repo = serializer.save()
        from .tasks import clone_repository_task
        clone_repository_task.delay(str(repo.id))

    @action(detail=True, methods=['post'])
    def index(self, request, pk=None):
        repo = self.get_object()
        if repo.status in (Repository.Status.CLONING, Repository.Status.INDEXING):
            return Response(
                {'detail': 'Repository is already being indexed.'},
                status=status.HTTP_409_CONFLICT,
            )
        from .tasks import clone_repository_task
        clone_repository_task.delay(str(repo.id))
        return Response({'status': 'indexing_started', 'repository_id': str(repo.id)})

    @action(detail=True, methods=['post'], url_path='reindex')
    def reindex(self, request, pk=None):
        repo = self.get_object()
        repo.indexed_files.all().delete()
        repo.file_count = 0
        repo.total_bytes = 0
        repo.status = Repository.Status.PENDING
        repo.save(update_fields=['file_count', 'total_bytes', 'status'])
        from .tasks import clone_repository_task
        clone_repository_task.delay(str(repo.id))
        return Response({'status': 'reindexing_started', 'repository_id': str(repo.id)})

    @action(detail=True, methods=['get'], url_path='status')
    def status_detail(self, request, pk=None):
        repo = self.get_object()
        return Response({
            'id': str(repo.id),
            'status': repo.status,
            'file_count': repo.file_count,
            'total_bytes': repo.total_bytes,
            'last_indexed_at': repo.last_indexed_at,
            'error_message': getattr(repo, 'error_message', None),
        })

    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        repo = self.get_object()
        files = repo.indexed_files.all().order_by('file_path')
        page = self.paginate_queryset(files)
        serializer = IndexedFileSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        repo = self.get_object()
        chunks = CodeChunk.objects.filter(
            file__repository=repo
        ).select_related('file').order_by('file__file_path', 'start_line')
        page = self.paginate_queryset(chunks)
        serializer = CodeChunkSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
