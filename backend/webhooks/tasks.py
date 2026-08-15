import hashlib
import hmac
import json
import logging

import httpx
from celery import shared_task

from .models import Webhook

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10.0


def send_webhook(webhook: Webhook, event: str, payload: dict) -> None:
    body = json.dumps(payload, separators=(',', ':'), default=str).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'X-CodeCoroner-Event': event,
        'X-CodeCoroner-Delivery': str(webhook.id),
    }
    if webhook.secret:
        signature = hmac.new(webhook.secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
        headers['X-CodeCoroner-Signature'] = f'sha256={signature}'

    resp = httpx.post(webhook.url, content=body, headers=headers, timeout=WEBHOOK_TIMEOUT)
    if resp.status_code >= 400:
        raise RuntimeError(f'Webhook returned HTTP {resp.status_code}: {resp.text[:200]}')


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def dispatch_webhook_task(self, webhook_id: str, event: str, payload: dict):
    try:
        webhook = Webhook.objects.get(id=webhook_id, is_active=True)
    except Webhook.DoesNotExist:
        logger.info('Webhook %s not found or inactive; dropping event %s', webhook_id, event)
        return

    try:
        send_webhook(webhook, event, payload)
        logger.info('Webhook %s delivered for event %s', webhook_id, event)
    except Exception as exc:
        logger.warning('Webhook %s failed for event %s: %s', webhook_id, event, exc)
        raise self.retry(exc=exc)  # noqa: B904
