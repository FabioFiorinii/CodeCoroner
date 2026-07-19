from agents.base_agent import BaseAgent

class EmbeddingGenerator(BaseAgent):
    async def run(self, chunks: list[dict]) -> dict:
        return {'status': 'not_implemented'}
