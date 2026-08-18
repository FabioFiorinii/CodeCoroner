from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User


class BruteForceLockoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/v1/auth/login/'
        User.objects.create_user(
            email='lockout@example.com',
            username='lockout',
            password='goodpass123',
        )
        User.objects.create_user(
            email='other@example.com',
            username='other',
            password='otherpass123',
        )

    def test_1_failed_attempts_return_400_until_limit(self):
        for _ in range(4):
            response = self.client.post(
                self.login_url,
                {'email': 'lockout@example.com', 'password': 'wrong'},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(
            self.login_url,
            {'email': 'lockout@example.com', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_2_lockout_blocks_correct_password(self):
        for _ in range(5):
            self.client.post(
                self.login_url,
                {'email': 'lockout@example.com', 'password': 'wrong'},
                format='json',
            )
        response = self.client.post(
            self.login_url,
            {'email': 'lockout@example.com', 'password': 'goodpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_3_other_user_not_affected_by_lockout(self):
        for _ in range(5):
            self.client.post(
                self.login_url,
                {'email': 'lockout@example.com', 'password': 'wrong'},
                format='json',
            )
        response = self.client.post(
            self.login_url,
            {'email': 'other@example.com', 'password': 'otherpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
