import json
import logging
import time

import httpx
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pgvector.django import CosineDistance

from repositories.models import ChunkEmbedding
from webhooks.services import dispatch

from .models import (
    Analysis,
    AnalysisRun,
    BugLocalization,
    FixSuggestion,
    Report,
    RootCause,
    SuspiciousFileScore,
)

logger = logging.getLogger(__name__)

AI_URL = getattr(settings, 'AI_ENGINE_URL', 'http://ai-engine:8002')


def _safe_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value, default=None):
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class AnalysisOrchestrator:
    def __init__(self, analysis: Analysis):
        self.analysis = analysis
        self.channel_layer = get_channel_layer()
        self.current_step = None
        self.model_llm, self.model_rca = self._resolve_models()

    def _resolve_models(self):
        try:
            from common.models import PlatformSetting

            tier = PlatformSetting.get_solo().model_tier
            cfg = settings.MODEL_TIERS.get(tier, {})
            return cfg.get('llm_model', ''), cfg.get('rca_model', '')
        except Exception:
            return '', ''

    def _fail_current_step(self, error):
        if self.current_step:
            AnalysisRun.objects.filter(analysis=self.analysis, step=self.current_step).update(
                status='failed', completed_at=timezone.now(), error=error
            )

    def _run_step(self, name, step_fn, status=None):
        if status:
            self._update_status(status)
        self.current_step = name
        self._record_run(name)
        try:
            step_fn()
            self._mark_completed(name)
            return True
        except Exception as exc:
            logger.exception(f'Step {name} failed for analysis {self.analysis.id}')
            self._fail_current_step(str(exc))
            return False

    def execute(self):
        start_time = time.time()
        try:
            ok = True
            ok &= self._run_step(
                'ensure_repo_indexed', self._ensure_repo_indexed, Analysis.Status.INDEXING
            )
            ok &= self._run_step('analyze_input', self._analyze_input, Analysis.Status.ANALYZING)
            ok &= self._run_step(
                'bug_localization', self._localize_bug, Analysis.Status.BUG_LOCALIZATION
            )
            ok &= self._run_step('root_cause', self._root_cause, Analysis.Status.RCA)
            ok &= self._run_step('generate_report', self._generate_report)
            ok &= self._run_step(
                'fix_suggestion', self._suggest_fix, Analysis.Status.FIX_SUGGESTION
            )

            if ok:
                self._update_status(Analysis.Status.COMPLETED)
                self.current_step = None
                self._record_run('completed', status='completed')
                dispatch(
                    self.analysis.project_id,
                    'analysis.completed',
                    {
                        'id': str(self.analysis.id),
                        'title': self.analysis.title,
                        'status': self.analysis.status,
                        'project': str(self.analysis.project_id),
                        'duration_seconds': int(time.time() - start_time),
                    },
                )
            else:
                failed_steps = list(
                    AnalysisRun.objects.filter(analysis=self.analysis, status='failed').values_list(
                        'step', flat=True
                    )
                )
                error = f'Some steps failed: {", ".join(failed_steps) or "unknown"}'
                self.analysis.status = Analysis.Status.FAILED
                self.analysis.error_message = error
                with transaction.atomic():
                    self.analysis.save(update_fields=['status', 'error_message'])
                self.current_step = None
                self._record_run('failed', status='failed', error=error)
                dispatch(
                    self.analysis.project_id,
                    'analysis.failed',
                    {
                        'id': str(self.analysis.id),
                        'title': self.analysis.title,
                        'status': self.analysis.status,
                        'project': str(self.analysis.project_id),
                        'error': error,
                    },
                )

        except Exception as e:
            logger.exception(f'Analysis {self.analysis.id} failed')
            self.analysis.status = Analysis.Status.FAILED
            self.analysis.error_message = str(e)
            with transaction.atomic():
                self.analysis.save(update_fields=['status', 'error_message'])
            self._record_run('failed', status='failed', error=str(e))
            dispatch(
                self.analysis.project_id,
                'analysis.failed',
                {
                    'id': str(self.analysis.id),
                    'title': self.analysis.title,
                    'status': self.analysis.status,
                    'project': str(self.analysis.project_id),
                    'error': str(e),
                },
            )
        finally:
            self.analysis.duration_seconds = int(time.time() - start_time)
            self.analysis.save(update_fields=['duration_seconds'])
            self._broadcast_status()

    def _update_status(self, status):
        self.analysis.status = status
        self.analysis.save(update_fields=['status'])
        self._broadcast_status()

    def _mark_completed(self, step):
        AnalysisRun.objects.filter(analysis=self.analysis, step=step).update(
            status='completed',
            completed_at=timezone.now(),
        )

    def _record_run(self, step, status='running', error=''):
        AnalysisRun.objects.update_or_create(
            analysis=self.analysis,
            step=step,
            defaults={
                'status': status,
                'error': error,
                'completed_at': timezone.now() if status in ('completed', 'failed') else None,
            },
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
                        'runs': list(
                            AnalysisRun.objects.filter(analysis=self.analysis).values(
                                'step', 'status', 'started_at', 'completed_at', 'error'
                            )
                        ),
                    },
                },
            )

    def _ensure_repo_indexed(self):
        from repositories.models import Repository

        repo = self.analysis.repository
        if repo.status != Repository.Status.INDEXED:
            from repositories.tasks import index_repository_task

            index_repository_task(str(repo.id))

    def _call_ai(self, endpoint: str, payload: dict, timeout: int = 600) -> dict:
        resp = httpx.post(f'{AI_URL}/{endpoint}', json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _analyze_input(self):
        result = self._call_ai(
            'analyze-logs',
            {
                'error_context': self.analysis.error_context,
                'model': self.model_llm,
            },
        )
        self.log_analysis = result
        AnalysisRun.objects.filter(analysis=self.analysis, step='analyze_input').update(
            output=result
        )

    def _retrieval_queries(self, ctx: dict) -> list[str]:
        fields = [ctx.get(key) for key in ('error_message', 'description', 'stacktrace', 'logs')]
        queries = []
        for _i, val in enumerate(fields):
            if isinstance(val, str) and val.strip():
                queries.append(val.strip())
        if fields[0] and fields[1]:
            queries.append(f'{fields[0].strip()}\n{fields[1].strip()}')
        return list(dict.fromkeys(q for q in queries if q)) or [json.dumps(ctx)]

    def _embed_query(self, text: str) -> list:
        resp = self._call_ai('embed', {'texts': [text], 'model': 'nomic-embed-text'})
        embeddings = resp.get('embeddings', [])
        if not embeddings:
            raise RuntimeError('Failed to get query embedding')
        return embeddings[0]

    def _retrieve_top_chunks(self, repo_id, query_vectors: list, limit: int = 30) -> list:
        base = ChunkEmbedding.objects.filter(chunk__file__repository_id=repo_id)
        merged: dict = {}
        for qvec in query_vectors:
            similar = (
                base.annotate(distance=CosineDistance('embedding', qvec))
                .select_related('chunk', 'chunk__file')
                .order_by('distance')[:15]
            )
            for ce in similar:
                cid = ce.chunk_id
                if cid not in merged or ce.distance < merged[cid][0]:
                    merged[cid] = (ce.distance, ce)
        ranked = sorted(merged.values(), key=lambda t: t[0])[:limit]
        return [t[1] for t in ranked]

    def _localize_bug(self):
        ctx = self.analysis.error_context
        query_vectors = [self._embed_query(q) for q in self._retrieval_queries(ctx)]

        repo_id = self.analysis.repository_id
        similar = self._retrieve_top_chunks(repo_id, query_vectors)

        chunks_for_ai = []
        for ce in similar:
            chunk = ce.chunk
            chunks_for_ai.append(
                {
                    'file_path': chunk.file.file_path,
                    'language': chunk.file.language,
                    'content': chunk.content,
                    'start_line': chunk.start_line,
                    'end_line': chunk.end_line,
                    'similarity': float(1.0 - ce.distance) if hasattr(ce, 'distance') else 0,
                }
            )
        self.top_chunks = chunks_for_ai

        result = self._call_ai(
            'localize-bug',
            {
                'repo_id': str(self.analysis.repository_id),
                'error_context': ctx,
                'log_analysis': self.log_analysis,
                'chunks': chunks_for_ai,
                'model': self.model_llm,
            },
        )
        self.localization_result = result

        suspicious = result.get('suspicious_files', [])
        if suspicious:
            bug_loc = BugLocalization.objects.create(
                analysis=self.analysis,
                summary=result.get('summary', ''),
            )
            for item in suspicious:
                SuspiciousFileScore.objects.create(
                    localization=bug_loc,
                    file_path=item.get('file_path', ''),
                    suspicion_score=_safe_float(item.get('score'), 0.0),
                    evidence=item.get('evidence', ''),
                    rank=_safe_int(item.get('rank'), 0),
                )

        AnalysisRun.objects.filter(analysis=self.analysis, step='bug_localization').update(
            output=result
        )

    def _root_cause(self):
        suspicious = []
        if hasattr(self.analysis, 'bug_localization'):
            suspicious = list(
                self.analysis.bug_localization.suspicious_files.all().values(
                    'file_path', 'suspicion_score', 'evidence', 'rank'
                )
            )

        top_paths = {s['file_path'] for s in suspicious[:5]}
        root_chunks = [c for c in getattr(self, 'top_chunks', []) if c['file_path'] in top_paths]

        result = self._call_ai(
            'analyze-root-cause',
            {
                'repo_id': str(self.analysis.repository_id),
                'error_context': self.analysis.error_context,
                'log_analysis': self.log_analysis,
                'suspicious_files': suspicious,
                'chunks': root_chunks,
                'model': self.model_rca,
            },
        )
        self.rca_result = result

        RootCause.objects.create(
            analysis=self.analysis,
            summary=result.get('summary', ''),
            root_file=result.get('root_file', ''),
            root_line=_safe_int(result.get('root_line')),
            cause_chain=result.get('cause_chain', ''),
            confidence=_safe_float(result.get('confidence'), 0.0),
            reasoning=result.get('reasoning', ''),
        )

        AnalysisRun.objects.filter(analysis=self.analysis, step='root_cause').update(output=result)

    def _generate_report(self):
        bug_loc = None
        if hasattr(self.analysis, 'bug_localization'):
            bl = self.analysis.bug_localization
            bug_loc = {
                'summary': bl.summary,
                'suspicious_files': list(
                    bl.suspicious_files.all().values(
                        'file_path', 'suspicion_score', 'evidence', 'rank'
                    )
                ),
            }

        rca = None
        if hasattr(self.analysis, 'root_cause'):
            rc = self.analysis.root_cause
            rca = {
                'summary': rc.summary,
                'root_file': rc.root_file,
                'root_line': rc.root_line,
                'cause_chain': rc.cause_chain,
                'confidence': rc.confidence,
                'reasoning': rc.reasoning,
            }

        repo_info = {
            'id': str(self.analysis.repository.id),
            'git_url': self.analysis.repository.git_url,
            'git_branch': self.analysis.repository.git_branch,
        }

        analysis_data = {
            'title': self.analysis.title,
            'error_context': self.analysis.error_context,
            'log_analysis': self.log_analysis,
            'bug_localization': bug_loc,
            'root_cause': rca,
            'repository': repo_info,
        }

        result = self._call_ai(
            'generate-report',
            {
                'analysis_data': analysis_data,
                'model': self.model_llm,
            },
        )

        Report.objects.create(
            analysis=self.analysis,
            markdown=result.get('markdown', ''),
            format='markdown',
        )

        AnalysisRun.objects.filter(analysis=self.analysis, step='generate_report').update(
            output=result
        )

    def _suggest_fix(self):
        bug_loc = None
        if hasattr(self.analysis, 'bug_localization'):
            bl = self.analysis.bug_localization
            bug_loc = {
                'summary': bl.summary,
                'suspicious_files': list(
                    bl.suspicious_files.all().values(
                        'file_path', 'suspicion_score', 'evidence', 'rank'
                    )
                ),
            }

        rca = None
        if hasattr(self.analysis, 'root_cause'):
            rc = self.analysis.root_cause
            rca = {
                'summary': rc.summary,
                'root_file': rc.root_file,
                'root_line': rc.root_line,
                'cause_chain': rc.cause_chain,
                'confidence': rc.confidence,
                'reasoning': rc.reasoning,
            }

        result = self._call_ai(
            'suggest-fix',
            {
                'error_context': self.analysis.error_context,
                'log_analysis': self.log_analysis,
                'bug_localization': bug_loc,
                'root_cause': rca,
                'chunks': getattr(self, 'top_chunks', [])[:5],
                'model': self.model_rca,
            },
        )

        FixSuggestion.objects.create(
            analysis=self.analysis,
            diff=result.get('diff', ''),
            plan=result.get('plan', ''),
            explanation=result.get('explanation', ''),
        )

        AnalysisRun.objects.filter(analysis=self.analysis, step='fix_suggestion').update(
            output=result
        )
