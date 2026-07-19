from agents.base_agent import BaseAgent

class RetrievalEngine(BaseAgent):
    async def run(self, query: str, repo_id: str, top_k: int = 20) -> dict:
        return {'status': 'not_implemented'}
