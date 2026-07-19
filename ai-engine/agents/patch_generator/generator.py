from agents.base_agent import BaseAgent

class PatchGenerator(BaseAgent):
    async def run(self, rca_result: dict, file_content: str) -> dict:
        return {'status': 'not_implemented'}
