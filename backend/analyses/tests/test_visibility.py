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


class AnalysisVisibilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/v1/analyses/'
        self.group_a = Group.objects.create(name='GroupA')
        self.group_b = Group.objects.create(name='GroupB')
        self.alice = User.objects.create_user(
            email='alice@t.com',
            username='alice',
            password='pass12345',
        )
        self.bob = User.objects.create_user(
            email='bob@t.com',
            username='bob',
            password='pass12345',
        )
        self.admin = User.objects.create_superuser(
            email='admin@t.com',
            username='admin',
            password='pass12345',
        )
        self.alice.groups.add(self.group_a)
        self.bob.groups.add(self.group_b)

        self.proj_a = Project.objects.create(name='ProjA', created_by=self.alice)
        self.proj_a.groups.add(self.group_a)
        ProjectMembership.objects.create(project=self.proj_a, user=self.alice, role='owner')
        self.proj_b = Project.objects.create(name='ProjB', created_by=self.bob)
        self.proj_b.groups.add(self.group_b)
        ProjectMembership.objects.create(project=self.proj_b, user=self.bob, role='owner')

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
            user=self.alice,
            project=self.proj_a,
            repository=self.repo_a,
            title='A bug',
        )
        self.analysis_b = Analysis.objects.create(
            user=self.bob,
            project=self.proj_b,
            repository=self.repo_b,
            title='B bug',
        )

    def test_1_admin_sees_all_analyses(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a['title'] for a in response.data['results']]
        self.assertIn('A bug', titles)
        self.assertIn('B bug', titles)

    def test_2_user_sees_only_own_group_analyses(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a['title'] for a in response.data['results']]
        self.assertIn('A bug', titles)
        self.assertNotIn('B bug', titles)

    def test_3_admin_retrieves_analysis_from_other_group(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/v1/analyses/{self.analysis_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'B bug')

    def test_4_create_blocked_when_repo_not_indexed(self):
        self.client.force_authenticate(user=self.alice)
        repo = Repository.objects.create(
            git_url='https://github.com/a/repo2.git',
            status=Repository.Status.INDEXING,
            project=self.proj_a,
        )
        with patch('analyses.tasks.run_analysis_pipeline.delay') as mock_pipeline:
            response = self.client.post(
                self.list_url,
                {
                    'project': str(self.proj_a.id),
                    'repository': str(repo.id),
                    'title': 'New',
                    'error_context': {'error_message': 'boom'},
                },
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not ready', str(response.data))
        mock_pipeline.assert_not_called()

    def test_5_create_blocked_when_any_repo_ids_not_indexed(self):
        self.client.force_authenticate(user=self.alice)
        repo_pending = Repository.objects.create(
            git_url='https://github.com/a/repo3.git',
            status=Repository.Status.PENDING,
            project=self.proj_a,
        )
        with patch('analyses.tasks.run_analysis_pipeline.delay') as mock_pipeline:
            response = self.client.post(
                self.list_url,
                {
                    'project': str(self.proj_a.id),
                    'repository': str(self.repo_a.id),
                    'repository_ids': [str(self.repo_a.id), str(repo_pending.id)],
                    'title': 'New',
                    'error_context': {'error_message': 'boom'},
                },
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not ready', str(response.data))
        mock_pipeline.assert_not_called()

    @patch('analyses.tasks.run_analysis_pipeline.delay')
    def test_6_create_allowed_when_repo_indexed(self, mock_pipeline):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            self.list_url,
            {
                'project': str(self.proj_a.id),
                'repository': str(self.repo_a.id),
                'title': 'New',
                'error_context': {'error_message': 'boom'},
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_pipeline.assert_called_once()
