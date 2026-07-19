from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'
        self.login_url = '/api/v1/auth/login/'
        self.me_url = '/api/v1/auth/me/'
        self.refresh_url = '/api/v1/auth/token/refresh/'
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
        }

    def test_1_register_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertEqual(response.data['username'], self.user_data['username'])
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)

    def test_2_register_duplicate_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_3_login_success(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_4_login_invalid_password(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': 'wrongpassword',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_5_login_nonexistent_user(self):
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@test.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_6_me_authenticated(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_resp = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        }, format='json')
        token = login_resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_7_me_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_8_token_refresh(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_resp = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        }, format='json')
        refresh_token = login_resp.data['refresh']
        response = self.client.post(self.refresh_url, {
            'refresh': refresh_token,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_9_login_missing_fields(self):
        response = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
