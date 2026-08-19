import json

from django.core.management.base import BaseCommand

from common.tasks import dlq_count, dlq_list, dlq_purge, dlq_replay


class Command(BaseCommand):
    help = 'Manage Celery Dead Letter Queue'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['list', 'count', 'replay', 'purge'],
            help='Action to perform',
        )
        parser.add_argument(
            '--task-id',
            type=str,
            help='Specific task ID to replay (for replay action)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit for list action',
        )

    def handle(self, *_args, **options):
        action = options['action']

        if action == 'count':
            count = dlq_count()
            self.stdout.write(f'DLQ entries: {count}')

        elif action == 'list':
            limit = options['limit']
            entries = dlq_list(limit)
            self.stdout.write(f'DLQ entries (limit {limit}): {len(entries)}')
            for entry in entries:
                self.stdout.write(
                    json.dumps(
                        {
                            'task_name': entry.get('task_name'),
                            'task_id': entry.get('task_id'),
                            'exception_type': entry.get('exception_type'),
                            'failed_at': entry.get('failed_at'),
                            'retries': entry.get('retries'),
                        },
                        indent=2,
                    )
                )

        elif action == 'replay':
            task_id = options.get('task_id')
            replayed = dlq_replay(task_id)
            self.stdout.write(f'Replayed {replayed} task(s)')

        elif action == 'purge':
            purged = dlq_purge()
            self.stdout.write(f'Purged {purged} DLQ entries')
