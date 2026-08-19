from django.db import migrations

from webhooks.crypto import encrypt_secret


def encrypt_existing_secrets(apps, _schema_editor):  # noqa: ARG001
    Webhook = apps.get_model('webhooks', 'Webhook')
    for webhook in Webhook.objects.exclude(secret=''):
        webhook.secret = encrypt_secret(webhook.secret)
        webhook.save(update_fields=['secret'])


def noop(apps, _schema_editor):  # noqa: ARG001
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('webhooks', '0002_alter_webhook_secret'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing_secrets, noop),
    ]
