import hashlib
import logging
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Repository, IndexedFile, CodeChunk, ChunkEmbedding
from .chunking import SemanticChunker
from .services import GitService

logger = logging.getLogger(__name__)

REPOS_ROOT = Path(settings.MEDIA_ROOT) / 'repos'
git_service = GitService()
chunker = SemanticChunker()

IGNORED_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    '.tox', '.eggs', 'dist', 'build', '.next', '.nuxt',
    'target', 'vendor', '.bundle', '.gradle', 'bin', 'obj',
    '.idea', '.vscode', '.DS_Store',
}

IGNORED_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe',
    '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg',
    '.woff', '.woff2', '.ttf', '.eot', '.pdf',
    '.zip', '.tar', '.gz', '.bz2', '.rar', '.7z',
    '.min.js', '.min.css', '.map',
}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def clone_repository_task(self, repo_id: str):
    try:
        repo = Repository.objects.get(id=repo_id)
    except Repository.DoesNotExist:
        logger.error('Repository %s not found', repo_id)
        return

    repo.status = Repository.Status.CLONING
    repo.save(update_fields=['status'])

    try:
        local_path = git_service.clone_or_pull(repo.git_url, repo.git_branch, repo_id)
        repo.local_path = str(local_path)
        repo.status = Repository.Status.INDEXING
        repo.save(update_fields=['local_path', 'status'])
        index_repository_task.delay(repo_id)
    except Exception as exc:
        logger.error('Clone/pull failed for %s: %s', repo_id, exc)
        _set_error(repo, f'Clone failed: {exc}')


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def index_repository_task(self, repo_id: str):
    try:
        repo = Repository.objects.get(id=repo_id)
    except Repository.DoesNotExist:
        return

    repo_path = Path(repo.local_path) if repo.local_path else REPOS_ROOT / repo_id
    if not repo_path.exists():
        _set_error(repo, 'Repository path not found')
        return

    repo.status = Repository.Status.INDEXING
    repo.save(update_fields=['status'])

    indexed = 0
    errors = 0
    total_bytes = 0
    seen_paths = set()

    for file_path in repo_path.rglob('*'):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(repo_path)
        seen_paths.add(str(rel).replace('\\', '/'))
        if any(p in IGNORED_DIRS for p in rel.parts):
            continue
        ext = file_path.suffix.lower()
        if ext in IGNORED_EXTENSIONS:
            continue
        language = chunker.detect_language(str(file_path))
        if language is None:
            continue

        try:
            content = file_path.read_bytes()
            file_hash = hashlib.sha256(content).hexdigest()
            total_bytes += len(content)
        except Exception as exc:
            logger.warning('Cannot read %s: %s', rel, exc)
            errors += 1
            continue

        indexed_file, _ = IndexedFile.objects.update_or_create(
            repository=repo,
            file_path=str(rel),
            defaults={'language': language, 'file_hash': file_hash},
        )

        chunks = _chunk_source(indexed_file, file_path, content, language)
        _save_chunks(indexed_file, chunks)
        indexed += 1

    repo.file_count = indexed
    repo.total_bytes = total_bytes
    repo.save(update_fields=['file_count', 'total_bytes'])

    stale = repo.indexed_files.exclude(file_path__in=seen_paths)
    if stale.exists():
        deleted = stale.count()
        stale.delete()
        logger.info('Pruned %d stale files in repo %s', deleted, repo_id)

    logger.info('Indexed %d files in repo %s', indexed, repo_id)

    if indexed == 0 and errors == 0:
        _set_error(repo, 'No supported files found in repository')
        return

    generate_embeddings_task.delay(repo_id)


def _chunk_source(indexed_file: IndexedFile, file_path: Path, content: bytes, language: str) -> list[dict]:
    try:
        source = content.decode('utf-8')
    except UnicodeDecodeError:
        source = content.decode('latin-1')
    return chunker.chunk_file(str(file_path), source, language)


def _save_chunks(indexed_file: IndexedFile, chunk_data: list[dict]):
    parent_map = {}
    for data in chunk_data:
        chunk_type = data.get('chunk_type', 'block')
        ct_map = {
            'module': CodeChunk.ChunkType.MODULE,
            'block': CodeChunk.ChunkType.BLOCK,
        }
        ct = ct_map.get(chunk_type, CodeChunk.ChunkType.BLOCK)

        parent_key = data.get('metadata', {}).get('parent_start')
        parent = parent_map.get(parent_key) if parent_key else parent_map.get('module')

        chunk = CodeChunk.objects.create(
            file=indexed_file,
            chunk_type=ct,
            start_line=data['start_line'],
            end_line=data['end_line'],
            content=data['content'],
            tokens_count=data.get('tokens_count', 0),
            metadata=data.get('metadata', {}),
            parent_chunk=parent,
        )

        if chunk_type == 'module' or (chunk_type == 'block' and parent is None):
            parent_map['module'] = chunk
            if 'parent_start' in data.get('metadata', {}):
                parent_map[data['metadata']['parent_start']] = chunk


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_embeddings_task(self, repo_id: str):
    try:
        repo = Repository.objects.get(id=repo_id)
    except Repository.DoesNotExist:
        return

    chunks = CodeChunk.objects.filter(
        file__repository=repo,
        embedding__isnull=True,
    ).select_related('file')

    total = chunks.count()
    if total == 0:
        _finish_index(repo)
        return

    batch_size = 32
    embedded = 0
    failed = 0

    for i in range(0, total, batch_size):
        batch = list(chunks[i:i + batch_size])
        texts = [c.content for c in batch]
        chunk_ids = [str(c.id) for c in batch]

        try:
            vectors = _call_embed_api(texts)
            if len(vectors) != len(chunk_ids):
                logger.warning('Mismatch: got %d vectors for %d texts', len(vectors), len(chunk_ids))
            for chunk_id, vector in zip(chunk_ids, vectors):
                ChunkEmbedding.objects.update_or_create(
                    chunk_id=chunk_id,
                    defaults={
                        'embedding': vector,
                        'model': 'nomic-embed-text',
                        'dimensions': 768,
                    },
                )
            embedded += len(batch)
        except Exception as exc:
            logger.error('Embedding batch failed for repo %s: %s', repo_id, exc)
            failed += len(batch)

    if failed == 0:
        _finish_index(repo)
    else:
        repo.status = Repository.Status.ERROR
        repo.error_message = f'{failed} chunks failed to embed'
        repo.save(update_fields=['status', 'error_message'])

    logger.info('Embedded %d chunks for repo %s (%d failed)', embedded, repo_id, failed)


def _finish_index(repo: Repository):
    repo.status = Repository.Status.INDEXED
    repo.last_indexed_at = timezone.now()
    repo.save(update_fields=['status', 'last_indexed_at'])


def _call_embed_api(texts: list[str]) -> list[list[float]]:
    import httpx
    ai_url = getattr(settings, 'AI_ENGINE_URL', 'http://ai-engine:8002')
    resp = httpx.post(
        f'{ai_url}/embed',
        json={'texts': texts, 'model': 'nomic-embed-text'},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()['embeddings']


def _set_error(repo: Repository, message: str):
    repo.status = Repository.Status.ERROR
    repo.error_message = message
    repo.save(update_fields=['status', 'error_message'])
    logger.error('[%s] %s', repo.id, message)


@shared_task(bind=True, max_retries=1)
def run_daily_pulls(self):
    repos = Repository.objects.filter(auto_pull=True)
    busy = (Repository.Status.CLONING, Repository.Status.INDEXING)
    pulled = skipped = 0
    for repo in repos:
        if repo.status in busy:
            skipped += 1
            continue
        try:
            local_path = git_service.clone_or_pull(repo.git_url, repo.git_branch, str(repo.id))
            repo.local_path = str(local_path)
            repo.status = Repository.Status.INDEXING
            repo.save(update_fields=['local_path', 'status'])
            index_repository_task(str(repo.id))
            pulled += 1
        except Exception as exc:
            logger.error('Daily pull failed for %s: %s', repo.id, exc)
            _set_error(repo, f'Pull failed: {exc}')
    logger.info('Daily pull: %d pulled, %d skipped', pulled, skipped)
