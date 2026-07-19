import time
import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import transaction

from .models import Analysis, AnalysisRun, BugLocalization, SuspiciousFileScore, RootCause, Report

logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    def __init__(self, analysis: Analysis):
        self.analysis = analysis
        self.channel_layer = get_channel_layer()

    def execute(self):
        start_time = time.time()
        try:
            self._update_status(Analysis.Status.INDEXING)
            self._record_run('ensure_repo_indexed')
            self._ensure_repo_indexed()

            self._update_status(Analysis.Status.ANALYZING)
            self._record_run('analyze_input')
            self._analyze_input()

            self._update_status(Analysis.Status.BUG_LOCALIZATION)
            self._record_run('bug_localization')
            self._localize_bug()

            self._update_status(Analysis.Status.RCA)
            self._record_run('root_cause')
            self._root_cause()

            self._update_status(Analysis.Status.COMPLETED)
            self._record_run('report', status='completed')

        except Exception as e:
            logger.exception(f'Analysis {self.analysis.id} failed')
            self.analysis.status = Analysis.Status.FAILED
            self.analysis.error_message = str(e)
            with transaction.atomic():
                self.analysis.save(update_fields=['status', 'error_message'])
            self._record_run('failed', status='failed', error=str(e))
        finally:
            self.analysis.duration_seconds = int(time.time() - start_time)
            self.analysis.save(update_fields=['duration_seconds'])
            self._broadcast_status()

    def _update_status(self, status):
        self.analysis.status = status
        self.analysis.save(update_fields=['status'])
        self._broadcast_status()

    def _record_run(self, step, status='running', error=''):
        AnalysisRun.objects.create(
            analysis=self.analysis,
            step=step,
            status=status,
            error=error,
        )
        self._broadcast_status()

    def _broadcast_status(self):
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                f'analysis_{self.analysis.id}',
                {
                    'type': 'status_update',
                    'data': {
                        'id': str(self.analysis.id),
                        'status': self.analysis.status,
                        'runs': list(AnalysisRun.objects.filter(
                            analysis=self.analysis
                        ).values('step', 'status', 'started_at', 'completed_at', 'error')),
                    },
                },
            )

    def _ensure_repo_indexed(self):
        from repositories.models import Repository
        repo = self.analysis.repository
        if repo.status != Repository.Status.INDEXED:
            from repositories.tasks import index_repository_task
            index_repository_task(str(repo.id))

    def _analyze_input(self):
        pass

    def _localize_bug(self):
        pass

    def _root_cause(self):
        pass
