from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from analyses.models import Analysis


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_model = get_user_model()
        group_ids = user.groups.all()
        team_members = user_model.objects.filter(groups__in=group_ids)
        if user.is_superuser:
            analyses = Analysis.objects.all()
        else:
            analyses = Analysis.objects.filter(user__groups__in=group_ids)

        recent = analyses.select_related('project').order_by('-created_at').distinct()[:5]
        recent_analyses = [
            {
                'id': a.id,
                'title': a.title,
                'status': a.status,
                'created_at': a.created_at,
                'duration_seconds': a.duration_seconds,
                'error_message': a.error_message,
                'project_id': a.project_id,
                'project_name': a.project.name,
            }
            for a in recent
        ]
        return Response(
            {
                'team_member_count': team_members.distinct().count(),
                'analyses_count': analyses.distinct().count(),
                'recent_analyses': recent_analyses,
            }
        )
