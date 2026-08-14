from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectMembership
from repositories.models import Repository, IndexedFile, CodeChunk
from repositories.chunking import SemanticChunker

User = get_user_model()


def _make_repo(project, **kwargs):
    return Repository.objects.create(
        project=project,
        git_url='https://github.com/user/repo.git',
        git_branch='main',
        **kwargs,
    )


class CloneTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@t.com', username='t', password='pass12345',
        )
        self.project = Project.objects.create(
            name='Test Project',
            created_by=self.user,
        )
        ProjectMembership.objects.create(
            project=self.project, user=self.user, role='owner',
        )
        self.repo = Repository.objects.create(
            project=self.project,
            git_url='https://github.com/user/repo.git',
            git_branch='main',
        )

    @patch('repositories.services.GitService.clone_or_pull')
    @patch('repositories.tasks.index_repository_task.delay')
    def test_clone_success(self, mock_index, mock_clone):
        mock_clone.return_value = None
        from repositories.tasks import clone_repository_task
        clone_repository_task(str(self.repo.id))

        self.repo.refresh_from_db()
        self.assertEqual(self.repo.status, Repository.Status.INDEXING)
        mock_index.assert_called_once_with(str(self.repo.id))

    @patch('repositories.services.GitService.clone_or_pull')
    def test_clone_failure(self, mock_clone):
        mock_clone.side_effect = Exception('git error')
        from repositories.tasks import clone_repository_task
        clone_repository_task(str(self.repo.id))

        self.repo.refresh_from_db()
        self.assertEqual(self.repo.status, Repository.Status.ERROR)
        self.assertIn('git error', self.repo.error_message)


class ChunkingTests(TestCase):
    def test_chunk_python_file(self):
        chunker = SemanticChunker()
        source = '''import os

def hello():
    print("hello")

class Calculator:
    def add(self, a, b):
        return a + b
'''
        chunks = chunker.chunk_file('/test.py', source, 'python')
        self.assertGreater(len(chunks), 0)
        types = [c['chunk_type'] for c in chunks]
        self.assertIn('module', types)

    def test_ignore_unsupported_language(self):
        chunker = SemanticChunker()
        lang = chunker.detect_language('file.wat')
        self.assertIsNone(lang)

    def test_small_file_no_split(self):
        chunker = SemanticChunker()
        source = 'x = 1\n'
        chunks = chunker.chunk_file('/t.py', source, 'python')
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['chunk_type'], 'module')


class IndexTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='t@t.com', username='t', password='pass12345',
        )
        self.project = Project.objects.create(
            name='Idx Project',
            created_by=self.user,
        )
        ProjectMembership.objects.create(
            project=self.project, user=self.user, role='owner',
        )
        self.repo = Repository.objects.create(
            project=self.project,
            git_url='https://github.com/user/repo.git',
            git_branch='main',
            local_path='/nonexistent',
        )

    def test_index_missing_path(self):
        from repositories.tasks import index_repository_task
        index_repository_task(str(self.repo.id))
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.status, Repository.Status.ERROR)

    def test_save_chunks(self):
        from repositories.tasks import _save_chunks
        indexed = IndexedFile.objects.create(
            repository=self.repo,
            file_path='test.py',
            language='python',
            file_hash='abc',
        )
        _save_chunks(indexed, [
            {
                'chunk_type': 'module',
                'start_line': 1,
                'end_line': 3,
                'content': 'a\nb\nc',
                'tokens_count': 3,
                'metadata': {},
            },
        ])
        count = CodeChunk.objects.filter(file=indexed).count()
        self.assertEqual(count, 1)


class PruneTaskTests(TestCase):
    def setUp(self):
        import tempfile
        self.user = User.objects.create_user(
            email='p@t.com', username='p', password='pass12345',
        )
        self.project = Project.objects.create(name='Prune Project', created_by=self.user)
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = Repository.objects.create(
            project=self.project,
            git_url='https://github.com/user/repo.git',
            git_branch='main',
            local_path=self.tmpdir.name,
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    @patch('repositories.tasks.generate_embeddings_task.delay')
    def test_prunes_stale_files(self, _mock_embed):
        path = __import__('pathlib').Path(self.tmpdir.name)
        (path / 'a.py').write_text('x = 1\n')
        (path / 'b.py').write_text('y = 2\n')

        stale = IndexedFile.objects.create(
            repository=self.repo, file_path='gone.py', language='python', file_hash='old',
        )
        keep = IndexedFile.objects.create(
            repository=self.repo, file_path='a.py', language='python', file_hash='old',
        )

        from repositories.tasks import index_repository_task
        index_repository_task(str(self.repo.id))

        self.assertFalse(IndexedFile.objects.filter(id=stale.id).exists())
        self.assertTrue(IndexedFile.objects.filter(id=keep.id).exists())
        self.assertEqual(IndexedFile.objects.filter(repository=self.repo).count(), 2)


class DailyPullTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='d@t.com', username='d', password='pass12345',
        )
        self.project = Project.objects.create(name='Daily Project', created_by=self.user)
        self.repo = _make_repo(self.project, auto_pull=True)
        self.off = _make_repo(self.project, auto_pull=False)
        self.busy = _make_repo(
            self.project, auto_pull=True, status=Repository.Status.INDEXING,
        )

    @patch('repositories.tasks.index_repository_task')
    @patch('repositories.services.GitService.clone_or_pull')
    def test_only_pulls_auto_pull_and_not_busy(self, mock_clone, mock_index):
        mock_clone.return_value = __import__('pathlib').Path('/tmp/repo')

        from repositories.tasks import run_daily_pulls
        run_daily_pulls()

        self.assertEqual(mock_clone.call_count, 1)
        self.assertEqual(mock_index.call_count, 1)
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.status, Repository.Status.INDEXING)

    @patch('repositories.tasks.index_repository_task')
    @patch('repositories.services.GitService.clone_or_pull')
    def test_pull_failure_sets_error(self, mock_clone, _mock_index):
        mock_clone.side_effect = Exception('pull failed')

        from repositories.tasks import run_daily_pulls
        run_daily_pulls()

        self.repo.refresh_from_db()
        self.assertEqual(self.repo.status, Repository.Status.ERROR)
        self.assertIn('pull failed', self.repo.error_message)
