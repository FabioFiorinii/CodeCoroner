from agents.base_agent import BaseAgent

class RootCauseAgent(BaseAgent):
    async def run(self, repo_id: str, error_context: dict, suspicious_files: list) -> dict:
        return {'status': 'not_implemented'}
