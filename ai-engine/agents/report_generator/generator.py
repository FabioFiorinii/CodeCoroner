from agents.base_agent import BaseAgent

class ReportGenerator(BaseAgent):
    async def run(self, analysis_data: dict) -> dict:
        return {'status': 'not_implemented'}
