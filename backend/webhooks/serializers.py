from rest_framework import serializers

from .constants import WEBHOOK_EVENT_NAMES
from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    events = serializers.ListField(
        child=serializers.ChoiceField(choices=WEBHOOK_EVENT_NAMES),
        allow_empty=True,
    )
    secret = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
        default='',
    )

    class Meta:
        model = Webhook
        fields = ['id', 'project', 'url', 'secret', 'events', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
