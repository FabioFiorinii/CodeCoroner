import logging
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

REPOS_ROOT = Path(settings.MEDIA_ROOT) / 'repos'


def git_gc_repos() -> int:
    """Run git gc --prune=now on every cloned repository; returns count."""
    count = 0
    if not REPOS_ROOT.exists():
        return count
    for repo_dir in REPOS_ROOT.iterdir():
        if not repo_dir.is_dir() or not (repo_dir / '.git').exists():
            continue
        try:
            subprocess.run(
                ['git', '-C', str(repo_dir), 'gc', '--quiet', '--prune=now'],
                check=True,
                capture_output=True,
                timeout=600,
            )
            count += 1
            logger.info('git gc done for %s', repo_dir.name)
        except Exception as exc:
            logger.warning('git gc failed for %s: %s', repo_dir.name, exc)
    return count


def prune_orphan_repo_dirs() -> int:
    """Remove cached repo dirs that no longer match any Repository row."""
    removed = 0
    if not REPOS_ROOT.exists():
        return removed
    from repositories.models import Repository

    known_ids = {str(pk) for pk in Repository.objects.values_list('id', flat=True)}
    for entry in REPOS_ROOT.iterdir():
        if entry.is_dir() and entry.name not in known_ids:
            logger.info('Removing orphaned repo dir %s', entry)
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
    return removed


def prune_old_analyses() -> int:
    """Delete analyses older than ANALYSIS_RETENTION_DAYS (0 disables retention)."""
    retention_days = getattr(settings, 'ANALYSIS_RETENTION_DAYS', 90)
    if not retention_days or retention_days <= 0:
        return 0
    cutoff = timezone.now() - timedelta(days=retention_days)
    from analyses.models import Analysis

    old = Analysis.objects.filter(created_at__lt=cutoff)
    count = old.count()
    if count:
        old.delete()
        logger.info('Deleted %d analyses older than %d days', count, retention_days)
    return count


def purge_stale_data() -> dict:
    return {
        'repos_gc': git_gc_repos(),
        'orphan_repo_dirs_removed': prune_orphan_repo_dirs(),
        'old_analyses_deleted': prune_old_analyses(),
    }
