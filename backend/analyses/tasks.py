import logging

from celery import shared_task

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
        self.retry(exc=exc)
