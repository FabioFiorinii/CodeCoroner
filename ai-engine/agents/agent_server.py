import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.config import AgentSettings
from core.ollama_client import OllamaClient
from agents.repository_indexer.indexer import RepositoryIndexer
from agents.embedding_generator.generator import EmbeddingGenerator
from agents.log_analyzer.analyzer import LogAnalyzer
from agents.bug_localizer.localizer import BugLocalizer
from agents.root_cause.rca_agent import RootCauseAgent
from agents.report_generator.generator import ReportGenerator
from agents.patch_generator.generator import PatchGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = AgentSettings()
ollama = OllamaClient(settings.ollama_base_url)
indexer = RepositoryIndexer()
embedder = EmbeddingGenerator()
log_analyzer = LogAnalyzer()
bug_localizer = BugLocalizer()
rca_agent = RootCauseAgent()
report_gen = ReportGenerator()
patch_gen = PatchGenerator()

_installed_cache: set[str] | None = None
_installed_cache_at = 0.0
INSTALLED_TTL = 30.0


async def installed_models():
    global _installed_cache, _installed_cache_at
    now = time.monotonic()
    if _installed_cache is not None and now - _installed_cache_at < INSTALLED_TTL:
        return _installed_cache
    models = await ollama.list_models()
    _installed_cache = set(models)
    _installed_cache_at = now
    return _installed_cache


async def resolve_model(requested: str | None, default: str) -> str:
    if not requested:
        return default
    try:
        installed = await installed_models()
        if requested in installed:
            return requested
        logger.warning(
            'Model %s is not installed, falling back to %s', requested, default
        )
        return default
    except Exception:
        logger.warning('Could not check installed models, using requested %s', requested)
        return requested


class EmbedRequest(BaseModel):
    texts: list[str]
    model: str = 'nomic-embed-text'


class IndexRequest(BaseModel):
    repo_path: str


class AnalyzeLogsRequest(BaseModel):
    error_context: dict
    model: str | None = None


class LocalizeBugRequest(BaseModel):
    repo_id: str
    error_context: dict
    log_analysis: dict
    chunks: list
    model: str | None = None


class RootCauseRequest(BaseModel):
    repo_id: str
    error_context: dict
    log_analysis: dict
    suspicious_files: list
    chunks: list
    model: str | None = None


class ReportRequest(BaseModel):
    analysis_data: dict
    model: str | None = None


class SuggestFixRequest(BaseModel):
    error_context: dict
    log_analysis: dict
    bug_localization: dict | None = None
    root_cause: dict | None = None
    chunks: list = []
    model: str | None = None


class PullModelRequest(BaseModel):
    model: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('AgentServer starting...')
    health = await ollama.health()
    logger.info('Ollama health: %s', health)
    yield
    await ollama.close()
    await embedder.close()
    logger.info('AgentServer stopped')


app = FastAPI(title='CodeCoroner AI Engine', version='0.1.0', lifespan=lifespan)


@app.get('/health')
async def health():
    healthy = await ollama.health()
    return {'status': 'healthy' if healthy else 'unhealthy', 'ollama': healthy}


@app.get('/models')
async def list_models():
    try:
        models = await ollama.list_models()
        return {'models': models}
    except Exception as exc:
        logger.error('List models failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/pull-model')
async def pull_model(req: PullModelRequest):
    global _installed_cache
    try:
        result = await ollama.pull(req.model)
        status = result.get('status', 'ok')
        if status != 'success':
            raise RuntimeError(f'Ollama pull returned status "{status}"')
        _installed_cache = None
        return {'status': 'ok', 'model': req.model}
    except Exception as exc:
        logger.error('Pull model %s failed: %s', req.model, exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/test-model')
async def test_model(req: PullModelRequest):
    try:
        await ollama.generate(req.model, 'Reply with the single word: ok')
        return {'status': 'ok', 'model': req.model}
    except Exception as exc:
        logger.error('Model test %s failed: %s', req.model, exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/embed')
async def embed(req: EmbedRequest):
    chunks = [{'content': t} for t in req.texts]
    embedder.settings.embed_model = req.model
    try:
        result = await embedder.run(chunks)
        if result['status'] == 'error' or result['failed'] == len(req.texts):
            raise HTTPException(status_code=502, detail='All embedding batches failed')
        return {
            'embeddings': result['embeddings'],
            'model': req.model,
            'count': result['count'],
            'failed': result['failed'],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('Embedding failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/index')
async def index(req: IndexRequest):
    result = await indexer.run(req.repo_path)
    if result.get('status') == 'error':
        raise HTTPException(status_code=400, detail=result.get('error'))
    return result


@app.post('/analyze-logs')
async def analyze_logs(req: AnalyzeLogsRequest):
    try:
        model = await resolve_model(req.model, settings.llm_model)
        log_analyzer.settings.llm_model = model
        result = await log_analyzer.run(req.error_context)
        if result.get('status') == 'error':
            raise HTTPException(status_code=502, detail=result.get('error', 'Log analysis failed'))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('Log analysis failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/localize-bug')
async def localize_bug(req: LocalizeBugRequest):
    try:
        model = await resolve_model(req.model, settings.llm_model)
        bug_localizer.settings.llm_model = model
        result = await bug_localizer.run(
            repo_id=req.repo_id,
            error_context=req.error_context,
            log_analysis=req.log_analysis,
            chunks=req.chunks,
        )
        if result.get('status') == 'error':
            raise HTTPException(status_code=502, detail=result.get('error', 'Bug localization failed'))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('Bug localization failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/analyze-root-cause')
async def analyze_root_cause(req: RootCauseRequest):
    try:
        model = await resolve_model(req.model, settings.rca_model)
        rca_agent.settings.rca_model = model
        result = await rca_agent.run(
            repo_id=req.repo_id,
            error_context=req.error_context,
            log_analysis=req.log_analysis,
            suspicious_files=req.suspicious_files,
            chunks=req.chunks,
        )
        if result.get('status') == 'error':
            raise HTTPException(status_code=502, detail=result.get('error', 'Root cause analysis failed'))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('Root cause analysis failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/suggest-fix')
async def suggest_fix(req: SuggestFixRequest):
    try:
        model = await resolve_model(req.model, settings.rca_model)
        patch_gen.settings.rca_model = model
        result = await patch_gen.run(
            error_context=req.error_context,
            log_analysis=req.log_analysis,
            bug_localization=req.bug_localization,
            root_cause=req.root_cause,
            chunks=req.chunks,
        )
        if result.get('status') == 'error':
            raise HTTPException(status_code=502, detail=result.get('error', 'Fix suggestion failed'))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('Fix suggestion failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post('/generate-report')
async def generate_report(req: ReportRequest):
    try:
        model = await resolve_model(req.model, settings.llm_model)
        report_gen.settings.llm_model = model
        result = await report_gen.run(req.analysis_data)
        if result.get('status') == 'error':
            raise HTTPException(status_code=502, detail=result.get('error', 'Report generation failed'))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('Report generation failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))
