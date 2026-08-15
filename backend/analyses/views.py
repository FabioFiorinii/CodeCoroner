from django.db.models import Count, Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Analysis
from .serializers import (
    AnalysisCreateSerializer,
    AnalysisSerializer,
    BugLocalizationSerializer,
    FixSuggestionSerializer,
    PatchSerializer,
    PatchValidationSerializer,
    ReportSerializer,
    RootCauseSerializer,
)


class AnalysisViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return AnalysisCreateSerializer
        return AnalysisSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Analysis.objects.filter(
            Q(project__memberships__user=user) | Q(project__groups__in=user.groups.all())
        )
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if self.action == 'list':
            qs = qs.filter(parent_analysis__isnull=True)
        qs = qs.annotate(children_count=Count('children', distinct=True))
        return (
            qs.distinct()
            .select_related('project', 'repository')
            .prefetch_related(
                'runs',
                'bug_localization__suspicious_files',
                'root_cause',
                'patch__validation',
                'fix_suggestion',
                'report',
            )
            .distinct()
        )

    def _thread(self, analysis):
        root = analysis.parent_analysis or analysis
        return [root, *root.children.order_by('created_at')]

    @action(detail=True, methods=['get', 'delete'], url_path='thread')
    def thread(self, request, pk=None):
        analysis = self.get_object()
        root = analysis.parent_analysis or analysis
        if request.method == 'DELETE':
            if not request.user.is_superuser and root.user != request.user:
                return Response(
                    {'detail': 'You do not have permission to delete this analysis.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            root.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AnalysisSerializer(self._thread(analysis), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis = serializer.save(user=self.request.user)
        from .tasks import run_analysis_pipeline

        run_analysis_pipeline.delay(str(analysis.id))
        from webhooks.services import dispatch

        dispatch(analysis.project_id, 'analysis.created', {
            'id': str(analysis.id),
            'title': analysis.title,
            'status': analysis.status,
            'project': str(analysis.project_id),
        })
        out = AnalysisSerializer(analysis, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        analysis = self.get_object()
        if not request.user.is_superuser and analysis.user != request.user:
            return Response(
                {'detail': 'You do not have permission to delete this analysis.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        analysis = self.get_object()
        return Response(
            {
                'id': analysis.id,
                'status': analysis.status,
                'runs': [
                    {
                        'step': r.step,
                        'status': r.status,
                        'started_at': r.started_at,
                        'completed_at': r.completed_at,
                    }
                    for r in analysis.runs.all()
                ],
                'created_at': analysis.created_at,
                'completed_at': analysis.completed_at,
                'duration_seconds': analysis.duration_seconds,
                'error_message': analysis.error_message,
            }
        )

    @action(detail=True, methods=['get'])
    def localization(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'bug_localization'):
            return Response(
                {'detail': 'Bug localization not available yet.'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = BugLocalizationSerializer(analysis.bug_localization)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def root_cause(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'root_cause'):
            return Response(
                {'detail': 'Root cause analysis not available yet.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = RootCauseSerializer(analysis.root_cause)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def patch(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'patch'):
            return Response(
                {'detail': 'Patch not available yet.'}, status=status.HTTP_404_NOT_FOUND
            )
        data = PatchSerializer(analysis.patch).data
        if hasattr(analysis.patch, 'validation'):
            data['validation'] = PatchValidationSerializer(analysis.patch.validation).data
        return Response(data)

    @action(detail=True, methods=['get'])
    def fix_suggestion(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'fix_suggestion'):
            return Response(
                {'detail': 'Fix suggestion not available yet.'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = FixSuggestionSerializer(analysis.fix_suggestion)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'report'):
            return Response(
                {'detail': 'Report not available yet.'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ReportSerializer(analysis.report)
        return Response(serializer.data)
