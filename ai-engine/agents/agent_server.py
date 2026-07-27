import logging
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


class EmbedRequest(BaseModel):
    texts: list[str]
    model: str = 'nomic-embed-text'


class IndexRequest(BaseModel):
    repo_path: str


class AnalyzeLogsRequest(BaseModel):
    error_context: dict


class LocalizeBugRequest(BaseModel):
    repo_id: str
    error_context: dict
    log_analysis: dict
    chunks: list


class RootCauseRequest(BaseModel):
    repo_id: str
    error_context: dict
    log_analysis: dict
    suspicious_files: list
    chunks: list


class ReportRequest(BaseModel):
    analysis_data: dict


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


@app.post('/generate-report')
async def generate_report(req: ReportRequest):
    try:
        result = await report_gen.run(req.analysis_data)
        if result.get('status') == 'error':
            raise HTTPException(status_code=502, detail=result.get('error', 'Report generation failed'))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('Report generation failed: %s', exc)
        raise HTTPException(status_code=502, detail=str(exc))
