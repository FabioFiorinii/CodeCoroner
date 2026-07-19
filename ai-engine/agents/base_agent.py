from abc import ABC, abstractmethod
from typing import Any
from core.ollama_client import OllamaClient
from core.config import AgentSettings

class BaseAgent(ABC):
    def __init__(self):
        self.settings = AgentSettings()
        self.ollama = OllamaClient(self.settings.ollama_base_url)

    @abstractmethod
    async def run(self, **kwargs) -> dict[str, Any]:
        pass

    async def close(self):
        await self.ollama.close()
