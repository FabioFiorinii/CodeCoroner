import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.config import AgentSettings
from core.ollama_client import OllamaClient
from agents.repository_indexer.indexer import RepositoryIndexer
from agents.embedding_generator.generator import EmbeddingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = AgentSettings()
ollama = OllamaClient(settings.ollama_base_url)
indexer = RepositoryIndexer()
embedder = EmbeddingGenerator()


class EmbedRequest(BaseModel):
    texts: list[str]
    model: str = 'nomic-embed-text'


class IndexRequest(BaseModel):
    repo_path: str


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
