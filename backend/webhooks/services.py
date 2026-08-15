import logging

logger = logging.getLogger(__name__)


def dispatch(project_id, event, payload):
    from .models import Webhook
    from .tasks import dispatch_webhook_task

    try:
        webhooks = list(
            Webhook.objects.filter(
                project_id=project_id,
                is_active=True,
                events__contains=event,
            )
        )
    except Exception:
        logger.exception('Webhook lookup failed for event %s', event)
        return

    for webhook in webhooks:
        try:
            dispatch_webhook_task.delay(str(webhook.id), event, payload)
        except Exception:
            logger.exception('Failed to enqueue webhook %s for event %s', webhook.id, event)
