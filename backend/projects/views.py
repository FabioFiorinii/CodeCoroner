from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer

class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'project'):
            project = obj.project
        else:
            project = obj
        return project.memberships.filter(user=request.user).exists()

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return Project.objects.filter(
            Q(created_by=self.request.user) |
            Q(memberships__user=self.request.user)
        ).distinct().prefetch_related('memberships__user')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def members(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            members = project.memberships.select_related('user').all()
            serializer = ProjectMembershipSerializer(members, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = ProjectMembershipSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='members/(?P<member_id>[^/.]+)')
    def remove_member(self, request, pk=None, member_id=None):
        project = self.get_object()
        membership = project.memberships.get(id=member_id)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
