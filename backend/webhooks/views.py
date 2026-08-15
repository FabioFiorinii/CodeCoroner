from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.views import IsSuperUser

from .models import Webhook
from .serializers import WebhookSerializer
from .tasks import send_webhook


class WebhookViewSet(viewsets.ModelViewSet):
    queryset = Webhook.objects.select_related('project').order_by('-created_at')
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        project = self.request.query_params.get('project')
        if project:
            queryset = queryset.filter(project_id=project)
        return queryset

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):  # noqa: ARG002
        webhook = self.get_object()
        payload = {
            'event': 'test.ping',
            'project': str(webhook.project_id),
            'message': 'Test ping from CodeCoroner',
        }
        try:
            send_webhook(webhook, 'test.ping', payload)
        except Exception as exc:
            return Response(
                {'detail': f'Test webhook failed: {exc}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({'detail': 'Test webhook delivered'})
