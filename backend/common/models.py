import uuid
from django.db import models

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PlatformSetting(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    model_tier = models.CharField(
        max_length=20,
        choices=[
            ('fast', 'Veloce'),
            ('balanced', 'Equilibrato'),
            ('precise', 'Preciso'),
        ],
        default='balanced',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Platform setting'
        verbose_name_plural = 'Platform settings'

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj
