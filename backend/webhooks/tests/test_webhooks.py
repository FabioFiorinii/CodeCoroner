import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project
from webhooks.models import Webhook
from webhooks.tasks import send_webhook

User = get_user_model()


class WebhookServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@test.com',
            username='owner',
            password='pass12345',
        )
        self.project = Project.objects.create(name='P1', created_by=self.user)
        self.webhook = Webhook.objects.create(
            project=self.project,
            url='https://hooks.example.com/codecoroner',
            secret='s3cr3t',
            events=['analysis.created', 'analysis.completed'],
        )

    @patch('webhooks.tasks.httpx.post')
    def test_send_webhook_signs_body_with_hmac(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text='ok')
        payload = {'id': 'abc', 'status': 'completed'}

        send_webhook(self.webhook, 'analysis.completed', payload)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        expected_body = json.dumps(payload, separators=(',', ':'), default=str).encode('utf-8')
        self.assertEqual(call_kwargs['content'], expected_body)
        expected_sig = hmac.new(b's3cr3t', expected_body, hashlib.sha256).hexdigest()
        self.assertEqual(
            call_kwargs['headers']['X-CodeCoroner-Signature'],
            f'sha256={expected_sig}',
        )
        self.assertEqual(call_kwargs['headers']['X-CodeCoroner-Event'], 'analysis.completed')
        self.assertEqual(mock_post.call_args.args[0], self.webhook.url)

    @patch('webhooks.tasks.httpx.post')
    def test_send_webhook_raises_on_error_status(self, mock_post):
        mock_post.return_value = Mock(status_code=500, text='boom')
        with self.assertRaises(RuntimeError):
            send_webhook(self.webhook, 'analysis.created', {})

    @patch('webhooks.tasks.dispatch_webhook_task.delay')
    def test_dispatch_only_enqueues_matching_active_webhooks(self, mock_delay):
        Webhook.objects.create(
            project=self.project,
            url='https://x/other',
            events=['repository.indexed'],
        )
        Webhook.objects.create(
            project=self.project,
            url='https://x/inactive',
            events=['analysis.created'],
            is_active=False,
        )
        Webhook.objects.create(
            project=self.project,
            url='https://x/no-secret',
            events=['analysis.completed'],
        )

        from webhooks.services import dispatch

        dispatch(self.project.id, 'analysis.completed', {'id': 'abc'})

        self.assertEqual(mock_delay.call_count, 2)

    @patch('webhooks.tasks.dispatch_webhook_task.delay')
    def test_dispatch_no_matches_does_not_enqueue(self, mock_delay):
        from webhooks.services import dispatch

        dispatch(self.project.id, 'analysis.failed', {'id': 'abc'})
        mock_delay.assert_not_called()


class WebhookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='u@test.com',
            username='u',
            password='pass12345',
        )
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='pass12345',
        )
        self.project = Project.objects.create(name='P1', created_by=self.admin)
        self.list_url = '/api/v1/webhooks/'

    def test_non_superuser_forbidden(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.list_url,
            {
                'project': str(self.project.id),
                'url': 'https://x/hook',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_create_and_list(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self.list_url,
            {
                'project': str(self.project.id),
                'url': 'https://hooks.example.com/codecoroner',
                'secret': 's3cr3t',
                'events': ['analysis.created'],
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('secret', resp.data)

        webhook = Webhook.objects.get(id=resp.data['id'])
        self.assertEqual(webhook.secret, 's3cr3t')
        self.assertEqual(webhook.events, ['analysis.created'])

        list_resp = self.client.get(f'{self.list_url}?project={self.project.id}')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data['results']), 1)

    @patch('webhooks.views.send_webhook')
    def test_test_action_reports_success(self, mock_send):
        webhook = Webhook.objects.create(project=self.project, url='https://x/hook')
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(f'{self.list_url}{webhook.id}/test/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        mock_send.assert_called_once()

    def test_invalid_event_rejected(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self.list_url,
            {
                'project': str(self.project.id),
                'url': 'https://x/hook',
                'events': ['bogus.event'],
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
