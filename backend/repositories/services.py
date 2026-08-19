import hashlib
from pathlib import Path

from django.conf import settings
from git import GitCommandError, Repo

REPO_CACHE_DIR = Path(settings.MEDIA_ROOT) / 'repos'


class GitService:
    def clone_or_pull(self, git_url: str, branch: str = 'main', repo_id: str | None = None) -> Path:
        local_path = REPO_CACHE_DIR / (repo_id or hashlib.sha256(git_url.encode()).hexdigest()[:16])
        if local_path.exists():
            try:
                repo = Repo(local_path)
                origin = repo.remotes.origin
                origin.pull(branch)
            except (GitCommandError, Exception):
                pass
        else:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            Repo.clone_from(git_url, local_path, branch=branch, depth=1)
        return local_path

    def get_file_tree(self, repo_path: Path) -> list[dict]:
        files = []
        for f in repo_path.rglob('*'):
            if f.is_file() and not f.name.startswith('.'):
                content = f.read_bytes()
                files.append(
                    {
                        'path': str(f.relative_to(repo_path)).replace('\\', '/'),
                        'size': len(content),
                        'hash': hashlib.sha256(content).hexdigest(),
                        'extension': f.suffix,
                    }
                )
        return files
