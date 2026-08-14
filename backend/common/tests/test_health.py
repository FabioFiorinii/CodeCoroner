from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse


class HealthTests(TestCase):
    @patch('common.views.httpx.get')
    def test_healthy_when_db_and_ai_engine_ok(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        resp = self.client.get(reverse('health'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'healthy')
        self.assertTrue(resp.data['database'])
        self.assertTrue(resp.data['ai_engine'])

    @patch('common.views.httpx.get')
    def test_degraded_when_ai_engine_unreachable(self, mock_get):
        mock_get.side_effect = Exception('ai-engine down')
        resp = self.client.get(reverse('health'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'degraded')
        self.assertTrue(resp.data['database'])
        self.assertFalse(resp.data['ai_engine'])
