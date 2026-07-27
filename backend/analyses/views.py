from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Analysis
from .serializers import (
    AnalysisSerializer, AnalysisCreateSerializer,
    BugLocalizationSerializer, RootCauseSerializer,
    PatchSerializer, PatchValidationSerializer, ReportSerializer,
)

class AnalysisViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return AnalysisCreateSerializer
        return AnalysisSerializer

    def get_queryset(self):
        return Analysis.objects.filter(
            project__memberships__user=self.request.user
        ).select_related('project', 'repository').prefetch_related(
            'runs',
            'bug_localization__suspicious_files',
            'root_cause',
            'patch__validation',
            'report',
        ).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis = serializer.save(user=self.request.user)
        from .tasks import run_analysis_pipeline
        run_analysis_pipeline.delay(str(analysis.id))
        out = AnalysisSerializer(analysis, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        analysis = self.get_object()
        return Response({
            'id': analysis.id,
            'status': analysis.status,
            'runs': [
                {'step': r.step, 'status': r.status, 'started_at': r.started_at, 'completed_at': r.completed_at}
                for r in analysis.runs.all()
            ],
            'created_at': analysis.created_at,
            'completed_at': analysis.completed_at,
            'duration_seconds': analysis.duration_seconds,
            'error_message': analysis.error_message,
        })

    @action(detail=True, methods=['get'])
    def localization(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'bug_localization'):
            return Response({'detail': 'Bug localization not available yet.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BugLocalizationSerializer(analysis.bug_localization)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def root_cause(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'root_cause'):
            return Response({'detail': 'Root cause analysis not available yet.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RootCauseSerializer(analysis.root_cause)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def patch(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'patch'):
            return Response({'detail': 'Patch not available yet.'}, status=status.HTTP_404_NOT_FOUND)
        data = PatchSerializer(analysis.patch).data
        if hasattr(analysis.patch, 'validation'):
            data['validation'] = PatchValidationSerializer(analysis.patch.validation).data
        return Response(data)

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        analysis = self.get_object()
        if not hasattr(analysis, 'report'):
            return Response({'detail': 'Report not available yet.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReportSerializer(analysis.report)
        return Response(serializer.data)
