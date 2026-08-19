from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project, ProjectMembership

User = get_user_model()


class ProjectCrudTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/v1/projects/'
        self.user = User.objects.create_user(
            email='owner@test.com',
            username='owner',
            password='pass12345',
        )
        self.other = User.objects.create_user(
            email='other@test.com',
            username='other',
            password='pass12345',
        )
        self.client.force_authenticate(user=self.user)

    def _detail_url(self, project_id):
        return f'/api/v1/projects/{project_id}/'

    def test_1_create_project(self):
        response = self.client.post(
            self.list_url,
            {
                'name': 'My Project',
                'description': 'A test project',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My Project')
        self.assertEqual(response.data['member_count'], 1)
        self.assertIn('id', response.data)

        project = Project.objects.get(id=response.data['id'])
        self.assertEqual(project.created_by, self.user)
        self.assertTrue(
            ProjectMembership.objects.filter(
                project=project,
                user=self.user,
                role='owner',
            ).exists()
        )

    def test_2_list_own_projects(self):
        Project.objects.create(name='P1', created_by=self.user)
        Project.objects.create(name='P2', created_by=self.other)
        Project.objects.create(name='P3', created_by=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data['results']]
        self.assertIn('P1', names)
        self.assertNotIn('P2', names)
        self.assertIn('P3', names)

    def test_3_retrieve_project(self):
        project = Project.objects.create(name='Test', created_by=self.user)
        ProjectMembership.objects.create(project=project, user=self.user, role='owner')
        response = self.client.get(self._detail_url(project.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test')

    def test_4_retrieve_non_member_returns_404(self):
        project = Project.objects.create(name='Secret', created_by=self.other)
        ProjectMembership.objects.create(project=project, user=self.other, role='owner')
        response = self.client.get(self._detail_url(project.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_5_update_project(self):
        project = Project.objects.create(name='Old Name', created_by=self.user)
        ProjectMembership.objects.create(project=project, user=self.user, role='owner')
        response = self.client.patch(
            self._detail_url(project.id),
            {
                'name': 'New Name',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'New Name')

    def test_6_delete_project(self):
        project = Project.objects.create(name='To Delete', created_by=self.user)
        ProjectMembership.objects.create(project=project, user=self.user, role='owner')
        response = self.client.delete(self._detail_url(project.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_7_list_members(self):
        project = Project.objects.create(name='Team', created_by=self.user)
        ProjectMembership.objects.create(project=project, user=self.user, role='owner')
        ProjectMembership.objects.create(project=project, user=self.other, role='member')
        response = self.client.get(f'{self._detail_url(project.id)}members/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_8_create_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, {'name': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_9_unauthenticated_list_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_10_admin_sees_all_projects(self):
        admin = User.objects.create_superuser(
            email='admin@t.com',
            username='admin',
            password='pass12345',
        )
        self.client.force_authenticate(user=admin)
        Project.objects.create(name='P1', created_by=self.user)
        Project.objects.create(name='P2', created_by=self.other)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data['results']]
        self.assertIn('P1', names)
        self.assertIn('P2', names)

    def test_11_admin_retrieves_project_of_other_group(self):
        admin = User.objects.create_superuser(
            email='admin@t.com',
            username='admin',
            password='pass12345',
        )
        self.client.force_authenticate(user=admin)
        project = Project.objects.create(name='Others', created_by=self.other)
        ProjectMembership.objects.create(project=project, user=self.other, role='owner')
        response = self.client.get(self._detail_url(project.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Others')
