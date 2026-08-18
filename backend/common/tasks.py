import logging

from celery import shared_task

from .cleanup import purge_stale_data

logger = logging.getLogger(__name__)


@shared_task
def purge_stale_data_task():
    logger.info('Starting periodic stale-data purge...')
    summary = purge_stale_data()
    logger.info('Purge complete: %s', summary)
    return summary
