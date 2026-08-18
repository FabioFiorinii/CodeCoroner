from django.core.management.base import BaseCommand

from common.cleanup import purge_stale_data


class Command(BaseCommand):
    help = 'Purge stale cached repos (git gc), orphaned repo dirs, and old analyses.'

    def handle(self, *args, **options):  # noqa: ARG002
        summary = purge_stale_data()
        for key, value in summary.items():
            self.stdout.write(f'{key}: {value}')
