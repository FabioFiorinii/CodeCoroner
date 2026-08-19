from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from repositories.models import Repository
from repositories.serializers import RepositorySerializer

from .models import Project, ProjectMembership
from .serializers import ProjectMembershipSerializer, ProjectSerializer


def _is_owner(request, project):
    if request.user.is_superuser:
        return True
    return project.memberships.filter(
        user=request.user,
        role=ProjectMembership.Role.OWNER,
    ).exists()


class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, _view, obj):  # noqa: ARG002
        if request.user.is_superuser:
            return True
        project = obj.project if hasattr(obj, 'project') else obj
        if project.memberships.filter(user=request.user).exists():
            return True
        return project.groups.filter(id__in=request.user.groups.all()).exists()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = Project.objects.all()
        else:
            qs = Project.objects.filter(
                Q(created_by=user) | Q(memberships__user=user) | Q(groups__in=user.groups.all())
            )
        return qs.distinct().prefetch_related('memberships__user').order_by('-created_at')

    @action(detail=True, methods=['get', 'post'])
    def members(self, request, pk=None):  # noqa: ARG002
        project = self.get_object()
        if request.method == 'GET':
            members = project.memberships.select_related('user').all()
            serializer = ProjectMembershipSerializer(members, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            if not _is_owner(request, project):
                return Response(
                    {'detail': 'Only project owners can manage members.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = ProjectMembershipSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='members/(?P<member_id>[^/.]+)')
    def remove_member(self, request, pk=None, member_id=None):  # noqa: ARG002
        project = self.get_object()
        if not _is_owner(request, project):
            return Response(
                {'detail': 'Only project owners can manage members.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        membership = project.memberships.get(id=member_id)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'], url_path='assign-repos')
    def assign_repos(self, request, pk=None):  # noqa: ARG002
        project = self.get_object()
        if request.method == 'GET':
            repos = project.assigned_repositories.all()
            serializer = RepositorySerializer(repos, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            if not _is_owner(request, project):
                return Response(
                    {'detail': 'Only project owners can manage repository assignments.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            repo_ids = request.data.get('repository_ids', [])
            repos = Repository.objects.filter(id__in=repo_ids)
            for repo in repos:
                if repo.project_id and repo.project_id != project.id:
                    return Response(
                        {'detail': 'Cannot assign a repository owned by another project.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            project.assigned_repositories.set(repos)
            for repo in repos:
                repo.groups.add(*project.groups.all())
            return Response({'status': 'ok', 'assigned_count': repos.count()})
