from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Repository, IndexedFile, CodeChunk
from .serializers import RepositorySerializer, IndexedFileSerializer, CodeChunkSerializer

class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.project.memberships.filter(user=request.user).exists()

class RepositoryViewSet(viewsets.ModelViewSet):
    serializer_class = RepositorySerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return Repository.objects.filter(
            project__memberships__user=self.request.user
        ).select_related('project').distinct()

    @action(detail=True, methods=['post'])
    def index(self, request, pk=None):
        repo = self.get_object()
        from .tasks import index_repository_task
        index_repository_task.delay(str(repo.id))
        return Response({'status': 'indexing_started'})

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
