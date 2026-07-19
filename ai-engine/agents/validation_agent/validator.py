from agents.base_agent import BaseAgent

class ValidationAgent(BaseAgent):
    async def run(self, patch_diff: str, repo_id: str) -> dict:
        return {'status': 'not_implemented'}
