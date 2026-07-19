import asyncio
import json
import logging
from httpx import ASGITransport
from core.ollama_client import OllamaClient
from core.config import AgentSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentServer:
    def __init__(self):
        self.settings = AgentSettings()
        self.ollama = OllamaClient(self.settings.ollama_base_url)

    async def health_check(self):
        healthy = await self.ollama.health()
        return {'status': 'healthy' if healthy else 'unhealthy', 'ollama': healthy}

    async def run(self):
        logger.info('Starting AgentServer...')
        health = await self.health_check()
        logger.info(f'Health: {health}')
        while True:
            await asyncio.sleep(60)
            logger.debug('AgentServer heartbeat')

async def main():
    server = AgentServer()
    await server.run()

if __name__ == '__main__':
    asyncio.run(main())
