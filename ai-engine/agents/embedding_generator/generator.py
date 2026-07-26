import logging
from typing import Any

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EmbeddingGenerator(BaseAgent):
    async def run(self, chunks: list[dict]) -> dict[str, Any]:
        model = self.settings.embed_model
        batch_size = self.settings.batch_size
        total = len(chunks)

        if total == 0:
            return {'status': 'ok', 'embeddings': [], 'count': 0, 'failed': 0}

        embeddings = []
        failed = 0

        for i in range(0, total, batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.get('content', c.get('text', str(c))) for c in batch]
            try:
                batch_embeddings = await self.ollama.embed(model, texts)
                embeddings.extend(batch_embeddings)
            except Exception as exc:
                logger.error('Batch %d-%d failed: %s', i, i + len(batch), exc)
                for _ in batch:
                    embeddings.append([])
                failed += len(batch)

        return {
            'status': 'ok' if failed == 0 else 'partial',
            'embeddings': embeddings,
            'count': total,
            'failed': failed,
            'model': model,
        }
