import logging
from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def run_analysis_pipeline(self, analysis_id: str):
    from .models import Analysis
    from .orchestrator import AnalysisOrchestrator
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        orchestrator = AnalysisOrchestrator(analysis)
        orchestrator.execute()
    except Analysis.DoesNotExist:
        logger.error(f'Analysis {analysis_id} not found')
    except Exception as exc:
        logger.exception(f'Pipeline failed for analysis {analysis_id}')
        raise self.retry(exc=exc)

@shared_task(bind=True, max_retries=3)
def index_repository_task(self, repo_id: str):
    from repositories.models import Repository
    from repositories.services import GitService
    from repositories.chunking import SemanticChunker
    try:
        repo = Repository.objects.get(id=repo_id)
        repo.status = Repository.Status.CLONING
        repo.save(update_fields=['status'])

        git_service = GitService()
        local_path = git_service.clone_or_pull(repo.git_url, repo.git_branch, str(repo.id))

        repo.status = Repository.Status.INDEXING
        repo.local_path = str(local_path)
        repo.save(update_fields=['status', 'local_path'])

        file_tree = git_service.get_file_tree(local_path)
        repo.file_count = len(file_tree)
        repo.total_bytes = sum(f['size'] for f in file_tree)
        repo.status = Repository.Status.INDEXED
        repo.last_indexed_at = __import__('django.utils.timezone', fromlist=['now']).now()
        repo.save(update_fields=['file_count', 'total_bytes', 'status', 'last_indexed_at'])

        logger.info(f'Repository {repo_id} indexed successfully ({repo.file_count} files)')
    except Exception as e:
        logger.exception(f'Indexing failed for repo {repo_id}')
        Repository.objects.filter(id=repo_id).update(status=Repository.Status.ERROR)

@shared_task(bind=True, max_retries=3)
def generate_embeddings_task(self, chunk_ids):
    pass

@shared_task(bind=True, max_retries=3)
def bug_localization_task(self, analysis_id: str):
    pass

@shared_task(bind=True, max_retries=3)
def root_cause_task(self, analysis_id: str):
    pass

@shared_task(bind=True, max_retries=3)
def generate_patch_task(self, analysis_id: str):
    pass

@shared_task(bind=True, max_retries=3)
def validate_patch_task(self, patch_id: str):
    pass

@shared_task(bind=True, max_retries=3)
def generate_report_task(self, analysis_id: str):
    pass
