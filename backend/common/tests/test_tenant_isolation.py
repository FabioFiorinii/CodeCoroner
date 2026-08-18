from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from analyses.models import Analysis
from projects.models import Project, ProjectMembership
from repositories.models import Repository

User = get_user_model()


class TenantIsolationTests(TestCase):
    """Cross-tenant isolation: users must never read or mutate other tenants' data."""

    def setUp(self):
        self.client = APIClient()
        self.group_a = Group.objects.create(name='GroupA')
        self.group_b = Group.objects.create(name='GroupB')
        self.alice = User.objects.create_user(
            email='alice@t.com', username='alice', password='pass12345',
        )
        self.bob = User.objects.create_user(
            email='bob@t.com', username='bob', password='pass12345',
        )
        self.alice.groups.add(self.group_a)
        self.bob.groups.add(self.group_b)

        self.proj_a = Project.objects.create(name='ProjA', created_by=self.alice)
        self.proj_a.groups.add(self.group_a)
        self.alice_membership = ProjectMembership.objects.create(
            project=self.proj_a, user=self.alice, role=ProjectMembership.Role.OWNER,
        )
        self.proj_b = Project.objects.create(name='ProjB', created_by=self.bob)
        self.proj_b.groups.add(self.group_b)
        ProjectMembership.objects.create(
            project=self.proj_b, user=self.bob, role=ProjectMembership.Role.OWNER,
        )

        self.repo_a = Repository.objects.create(
            git_url='https://github.com/a/repo.git',
            status=Repository.Status.INDEXED,
            project=self.proj_a,
        )
        self.repo_b = Repository.objects.create(
            git_url='https://github.com/b/repo.git',
            status=Repository.Status.INDEXED,
            project=self.proj_b,
        )

        self.analysis_a = Analysis.objects.create(
            user=self.alice, project=self.proj_a, repository=self.repo_a, title='A bug',
        )
        self.analysis_b = Analysis.objects.create(
            user=self.bob, project=self.proj_b, repository=self.repo_b, title='B bug',
        )

    def _analysis_url(self, analysis_id, suffix=''):
        return f'/api/v1/analyses/{analysis_id}/{suffix}'

    # --- analyses: cross-tenant reads/writes on the main object ---

    def test_1_cross_tenant_analysis_detail_returns_404(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(self._analysis_url(self.analysis_a.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_2_cross_tenant_analysis_patch_returns_404(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.patch(
            self._analysis_url(self.analysis_a.id), {'title': 'hacked'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.analysis_a.refresh_from_db()
        self.assertEqual(self.analysis_a.title, 'A bug')

    def test_3_cross_tenant_analysis_delete_returns_404(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.delete(self._analysis_url(self.analysis_a.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Analysis.objects.filter(id=self.analysis_a.id).exists())

    # --- analyses: subresources must also be tenant-scoped ---

    def test_4_cross_tenant_analysis_subresources_return_404(self):
        self.client.force_authenticate(user=self.bob)
        endpoints = [
            self._analysis_url(self.analysis_a.id, 'status/'),
            self._analysis_url(self.analysis_a.id, 'localization/'),
            self._analysis_url(self.analysis_a.id, 'root_cause/'),
            self._analysis_url(self.analysis_a.id, 'patch/'),
            self._analysis_url(self.analysis_a.id, 'fix_suggestion/'),
            self._analysis_url(self.analysis_a.id, 'report/'),
            self._analysis_url(self.analysis_a.id, 'thread/'),
        ]
        for url in endpoints:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_5_cross_tenant_thread_delete_returns_404(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.delete(self._analysis_url(self.analysis_a.id, 'thread/'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Analysis.objects.filter(id=self.analysis_a.id).exists())

    # --- analyses: creation must be tenant-scoped ---

    @patch('analyses.tasks.run_analysis_pipeline.delay')
    def test_6_cross_tenant_create_analysis_blocked(self, mock_pipeline):
        self.client.force_authenticate(user=self.bob)
        response = self.client.post('/api/v1/analyses/', {
            'project': str(self.proj_a.id),
            'repository': str(self.repo_a.id),
            'title': 'stolen',
            'error_context': {'error_message': 'boom'},
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_pipeline.assert_not_called()
        self.assertFalse(
            Analysis.objects.filter(
                project=self.proj_a, title='stolen',
            ).exists()
        )

    @patch('analyses.tasks.run_analysis_pipeline.delay')
    def test_7_cross_tenant_repo_in_own_project_blocked(self, mock_pipeline):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/v1/analyses/', {
            'project': str(self.proj_a.id),
            'repository': str(self.repo_b.id),
            'title': 'foreign-repo',
            'error_context': {'error_message': 'boom'},
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_pipeline.assert_not_called()

    @patch('analyses.tasks.run_analysis_pipeline.delay')
    def test_8_owner_create_analysis_in_own_project_allowed(self, mock_pipeline):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/v1/analyses/', {
            'project': str(self.proj_a.id),
            'repository': str(self.repo_a.id),
            'title': 'mine',
            'error_context': {'error_message': 'boom'},
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_pipeline.assert_called_once()

    # --- projects: membership management must be owner-only ---

    def test_9_member_cannot_add_owner(self):
        carol = User.objects.create_user(
            email='carol@t.com', username='carol', password='pass12345',
        )
        ProjectMembership.objects.create(
            project=self.proj_a, user=carol, role=ProjectMembership.Role.MEMBER,
        )
        self.client.force_authenticate(user=carol)
        response = self.client.post(
            f'/api/v1/projects/{self.proj_a.id}/members/',
            {'user': self.bob.id, 'role': ProjectMembership.Role.OWNER},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            ProjectMembership.objects.filter(project=self.proj_a, user=self.bob).exists()
        )

    def test_10_member_cannot_remove_owner(self):
        carol = User.objects.create_user(
            email='carol@t.com', username='carol', password='pass12345',
        )
        ProjectMembership.objects.create(
            project=self.proj_a, user=carol, role=ProjectMembership.Role.MEMBER,
        )
        self.client.force_authenticate(user=carol)
        response = self.client.delete(
            f'/api/v1/projects/{self.proj_a.id}/members/{self.alice_membership.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            ProjectMembership.objects.filter(id=self.alice_membership.id).exists()
        )

    def test_11_member_cannot_assign_repos(self):
        carol = User.objects.create_user(
            email='carol@t.com', username='carol', password='pass12345',
        )
        ProjectMembership.objects.create(
            project=self.proj_a, user=carol, role=ProjectMembership.Role.MEMBER,
        )
        self.client.force_authenticate(user=carol)
        response = self.client.post(
            f'/api/v1/projects/{self.proj_a.id}/assign-repos/',
            {'repository_ids': [str(self.repo_a.id)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_12_owner_cannot_assign_foreign_tenant_repo(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            f'/api/v1/projects/{self.proj_a.id}/assign-repos/',
            {'repository_ids': [str(self.repo_b.id)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            Repository.objects.get(id=self.repo_b.id).project_id == self.proj_a.id
        )
        self.assertFalse(self.proj_a.assigned_repositories.filter(id=self.repo_b.id).exists())

    def test_13_owner_can_assign_own_repo(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            f'/api/v1/projects/{self.proj_a.id}/assign-repos/',
            {'repository_ids': [str(self.repo_a.id)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.proj_a.assigned_repositories.filter(id=self.repo_a.id).exists())

    # --- webhooks: superuser-only, secret never serialized ---

    def test_14_non_superuser_cannot_access_webhooks(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.get('/api/v1/webhooks/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_15_webhook_secret_not_exposed_to_superuser(self):
        from webhooks.models import Webhook

        webhook = Webhook.objects.create(
            project=self.proj_a,
            url='https://example.com/hook',
            events=['analysis.created'],
            secret='supersecret',
        )
        admin = User.objects.create_superuser(
            email='admin@t.com', username='admin', password='pass12345',
        )
        self.client.force_authenticate(user=admin)
        response = self.client.get('/api/v1/webhooks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.content.decode()
        self.assertNotIn('supersecret', body)
        self.assertNotIn('enc:', body)
        webhook.refresh_from_db()
        self.assertTrue(webhook.secret.startswith('enc:'))
