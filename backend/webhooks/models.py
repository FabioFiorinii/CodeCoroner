import uuid
from django.db import models
from django.conf import settings

class Webhook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='webhooks',
    )
    url = models.URLField(max_length=2048)
    secret = models.CharField(max_length=255, blank=True, default='')
    events = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.project.name} → {self.url}'
