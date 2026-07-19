from agents.base_agent import BaseAgent

class RepositoryIndexer(BaseAgent):
    async def run(self, repo_path: str) -> dict:
        return {'status': 'not_implemented'}
