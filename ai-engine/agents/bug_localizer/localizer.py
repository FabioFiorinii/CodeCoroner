from agents.base_agent import BaseAgent

class BugLocalizer(BaseAgent):
    async def run(self, repo_id: str, error_context: dict) -> dict:
        return {'status': 'not_implemented'}
