import logging
import traceback
from datetime import datetime

from celery import Task

logger = logging.getLogger(__name__)


class DLQTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super().on_failure(exc, task_id, args, kwargs, einfo)

        dlq_payload = {
            'task_name': self.name,
            'task_id': task_id,
            'args': args,
            'kwargs': kwargs,
            'exception': str(exc),
            'exception_type': type(exc).__name__,
            'traceback': ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if exc.__traceback__
            else '',
            'retries': self.request.retries,
            'failed_at': datetime.utcnow().isoformat() + 'Z',
        }

        try:
            from celery import current_app

            current_app.send_task(
                'common.tasks.dlq_receiver',
                args=[dlq_payload],
                queue='celery_dlq',
            )
            logger.warning('Task %s (%s) sent to DLQ', self.name, task_id)
        except Exception as e:
            logger.error('Failed to send task %s to DLQ: %s', self.name, e)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        super().on_retry(exc, task_id, args, kwargs, einfo)
        logger.info('Task %s (%s) retry %d', self.name, task_id, self.request.retries)
