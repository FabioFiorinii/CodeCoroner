import json
import logging
import os

from celery import shared_task

from .cleanup import purge_stale_data

logger = logging.getLogger(__name__)

_DLQ_REDIS_KEY = 'codecoroner:dlq'


def _get_redis_client():
    import redis

    return redis.Redis.from_url(
        os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        decode_responses=True,
    )


@shared_task
def purge_stale_data_task():
    logger.info('Starting periodic stale-data purge...')
    summary = purge_stale_data()
    logger.info('Purge complete: %s', summary)
    return summary


@shared_task
def dlq_receiver(payload: dict):
    """Store failed task in Redis list for later inspection/replay."""
    client = _get_redis_client()
    client.rpush(_DLQ_REDIS_KEY, json.dumps(payload))
    logger.info(
        'DLQ entry stored for task %s (%s)', payload.get('task_name'), payload.get('task_id')
    )


def dlq_list(limit: int = 100) -> list[dict]:
    client = _get_redis_client()
    return [json.loads(item) for item in client.lrange(_DLQ_REDIS_KEY, 0, limit - 1)]


def dlq_count() -> int:
    client = _get_redis_client()
    return client.llen(_DLQ_REDIS_KEY)


def dlq_replay(task_id: str | None = None) -> int:
    """Replay tasks from DLQ. If task_id given, replay only that one; else replay all."""
    client = _get_redis_client()
    replayed = 0
    while True:
        item = client.lpop(_DLQ_REDIS_KEY)
        if not item:
            break
        payload = json.loads(item)
        if task_id and payload.get('task_id') != task_id:
            client.rpush(_DLQ_REDIS_KEY, item)
            break
        try:
            from celery import current_app

            current_app.send_task(
                payload['task_name'],
                args=payload.get('args', []),
                kwargs=payload.get('kwargs', {}),
                queue=payload.get('queue', 'celery'),
            )
            replayed += 1
            logger.info('Replayed task %s (%s)', payload['task_name'], payload['task_id'])
        except Exception as e:
            logger.error('Failed to replay task %s: %s', payload.get('task_name'), e)
            client.rpush(_DLQ_REDIS_KEY, item)
            break
    return replayed


def dlq_purge() -> int:
    client = _get_redis_client()
    count = client.llen(_DLQ_REDIS_KEY)
    client.delete(_DLQ_REDIS_KEY)
    logger.info('Purged %d DLQ entries', count)
    return count
