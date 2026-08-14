import os

from django.apps import AppConfig
from django.conf import settings


class RepositoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'repositories'

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(self._ensure_daily_pull_task, sender=self)

    @staticmethod
    def _ensure_daily_pull_task(sender, **kwargs):  # noqa: ARG004
        try:
            from django_celery_beat.models import CrontabSchedule, PeriodicTask
        except Exception:
            return

        hour = int(os.environ.get('AUTO_PULL_HOUR', settings.AUTO_PULL_HOUR))
        minute = int(os.environ.get('AUTO_PULL_MINUTE', settings.AUTO_PULL_MINUTE))

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=str(minute),
            hour=str(hour),
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        PeriodicTask.objects.update_or_create(
            name='repositories.run_daily_pulls',
            defaults={
                'task': 'repositories.tasks.run_daily_pulls',
                'crontab': schedule,
                'enabled': True,
            },
        )
