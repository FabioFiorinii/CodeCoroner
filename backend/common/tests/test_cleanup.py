import subprocess
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from analyses.models import Analysis
from common import cleanup
from projects.models import Project
from repositories.models import Repository

User = get_user_model()


class CleanupTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@t.com',
            username='owner',
            password='pass12345',
        )
        self.project = Project.objects.create(name='P', created_by=self.user)
        self.repo = Repository.objects.create(
            project=self.project,
            git_url='https://example.com/repo.git',
        )

    def _analysis(self, days_ago):
        analysis = Analysis.objects.create(
            user=self.user,
            project=self.project,
            repository=self.repo,
            title='A',
        )
        Analysis.objects.filter(id=analysis.id).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )
        return analysis

    @override_settings(ANALYSIS_RETENTION_DAYS=90)
    def test_prune_old_analyses_deletes_only_expired(self):
        old = self._analysis(days_ago=200)
        recent = self._analysis(days_ago=5)

        deleted = cleanup.prune_old_analyses()

        self.assertEqual(deleted, 1)
        self.assertFalse(Analysis.objects.filter(id=old.id).exists())
        self.assertTrue(Analysis.objects.filter(id=recent.id).exists())

    @override_settings(ANALYSIS_RETENTION_DAYS=0)
    def test_prune_old_analyses_disabled_when_zero(self):
        old = self._analysis(days_ago=200)
        self.assertEqual(cleanup.prune_old_analyses(), 0)
        self.assertTrue(Analysis.objects.filter(id=old.id).exists())

    def test_prune_orphan_repo_dirs(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            orphan = Path(tmp) / 'not-a-repo-id'
            orphan.mkdir()
            known = Path(tmp) / str(self.repo.id)
            known.mkdir()
            with (
                patch.object(cleanup, 'REPOS_ROOT', Path(tmp)),
                patch('common.cleanup.shutil.rmtree') as mock_rmtree,
            ):
                removed = cleanup.prune_orphan_repo_dirs()
            self.assertEqual(removed, 1)
            mock_rmtree.assert_called_once_with(orphan, ignore_errors=True)
            self.assertTrue(known.exists())

    def test_git_gc_repos_with_real_repo(self):
        with patch.object(cleanup, 'REPOS_ROOT') as root:
            repo_dir = Path('/tmp/codecoroner-test-repo')
            repo_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(['git', 'init', '-q', str(repo_dir)], check=True)
            root.exists.return_value = True
            root.iterdir.return_value = [repo_dir]
            try:
                count = cleanup.git_gc_repos()
            finally:
                subprocess.run(['rm', '-rf', str(repo_dir)], check=True)
        self.assertEqual(count, 1)

    @patch('common.management.commands.purge_stale_data.purge_stale_data')
    def test_command_runs(self, mock_purge):
        mock_purge.return_value = {
            'repos_gc': 0,
            'orphan_repo_dirs_removed': 0,
            'old_analyses_deleted': 0,
        }
        call_command('purge_stale_data')
        mock_purge.assert_called_once()
