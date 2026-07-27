import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = 'http://ollama:11434'):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def generate(self, model: str, prompt: str, **kwargs) -> str:
        response = await self.client.post('/api/generate', json={
            'model': model,
            'prompt': prompt,
            'stream': False,
            **kwargs,
        })
        response.raise_for_status()
        return response.json()['response']

    async def embed(self, model: str, input_text: str | list[str]) -> list[float] | list[list[float]]:
        inputs = input_text if isinstance(input_text, list) else [input_text]
        embeddings = []
        for text in inputs:
            try:
                response = await self.client.post('/api/embeddings', json={
                    'model': model,
                    'prompt': text,
                })
                response.raise_for_status()
                data = response.json()
                embeddings.append(data['embedding'])
            except Exception:
                logger.warning('Embedding failed for text (len=%d), returning zero vector', len(text))
                embeddings.append([0.0] * 768)
        if isinstance(input_text, str):
            return embeddings[0]
        return embeddings

    async def health(self) -> bool:
        try:
            response = await self.client.get('/api/tags')
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()
