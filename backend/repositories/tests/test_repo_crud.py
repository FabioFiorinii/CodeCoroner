from unittest.mock import patch
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectMembership
from repositories.models import Repository

User = get_user_model()


class RepoCrudTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/v1/repositories/'
        self.user = User.objects.create_user(
            email='owner@t.com', username='owner', password='pass12345',
        )
        self.other = User.objects.create_user(
            email='other@t.com', username='other', password='pass12345',
        )
        self.project = Project.objects.create(name='Test Project', created_by=self.user)
        ProjectMembership.objects.create(project=self.project, user=self.user, role='owner')
        self.client.force_authenticate(user=self.user)

    def _detail_url(self, repo_id):
        return f'/api/v1/repositories/{repo_id}/'

    @patch('repositories.tasks.clone_repository_task.delay')
    def test_1_create_repo_as_member(self, mock_clone):
        response = self.client.post(self.list_url, {
            'project': str(self.project.id),
            'git_url': 'https://github.com/user/repo.git',
            'git_branch': 'main',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['git_url'], 'https://github.com/user/repo.git')
        repo = Repository.objects.get(id=response.data['id'])
        self.assertEqual(repo.status, 'pending')
        mock_clone.assert_called_once_with(str(repo.id))

    @patch('repositories.tasks.clone_repository_task.delay')
    def test_2_create_repo_default_branch(self, mock_clone):
        response = self.client.post(self.list_url, {
            'project': str(self.project.id),
            'git_url': 'https://github.com/user/repo.git',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['git_branch'], 'main')
        mock_clone.assert_called_once()

    def test_3_create_repo_as_non_member(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(self.list_url, {
            'project': str(self.project.id),
            'git_url': 'https://github.com/user/repo.git',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_4_create_repo_invalid_git_url(self):
        response = self.client.post(self.list_url, {
            'project': str(self.project.id),
            'git_url': 'not-a-url',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get('errors', [])
        fields = [e['field'] for e in errors]
        self.assertIn('git_url', fields)

    def test_5_create_repo_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, {
            'project': str(self.project.id),
            'git_url': 'https://github.com/user/repo.git',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_6_list_repos(self):
        Repository.objects.create(project=self.project, git_url='https://github.com/a/b.git')
        Repository.objects.create(project=self.project, git_url='https://github.com/c/d.git')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_7_list_repos_excludes_other_project(self):
        p2 = Project.objects.create(name='P2', created_by=self.other)
        ProjectMembership.objects.create(project=p2, user=self.other, role='owner')
        Repository.objects.create(project=self.project, git_url='https://github.com/a/b.git')
        Repository.objects.create(project=p2, git_url='https://github.com/c/d.git')
        response = self.client.get(self.list_url)
        self.assertEqual(len(response.data['results']), 1)

    def test_8_retrieve_repo(self):
        repo = Repository.objects.create(project=self.project, git_url='https://github.com/a/b.git')
        response = self.client.get(self._detail_url(repo.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(repo.id))

    def test_9_retrieve_non_member_repo_returns_404(self):
        p2 = Project.objects.create(name='P2', created_by=self.other)
        ProjectMembership.objects.create(project=p2, user=self.other, role='owner')
        repo = Repository.objects.create(project=p2, git_url='https://github.com/secret/repo.git')
        response = self.client.get(self._detail_url(repo.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_10_delete_repo(self):
        repo = Repository.objects.create(project=self.project, git_url='https://github.com/a/b.git')
        response = self.client.delete(self._detail_url(repo.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Repository.objects.filter(id=repo.id).exists())

    def test_11_patch_repo(self):
        repo = Repository.objects.create(
            project=self.project, git_url='https://github.com/a/b.git', git_branch='main',
        )
        response = self.client.patch(self._detail_url(repo.id), {
            'git_branch': 'develop',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repo.refresh_from_db()
        self.assertEqual(repo.git_branch, 'develop')
