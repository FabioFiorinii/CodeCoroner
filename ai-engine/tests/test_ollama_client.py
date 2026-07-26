import pytest
from core.ollama_client import OllamaClient


class TestOllamaClient:
    @pytest.mark.asyncio
    async def test_health_returns_false_without_server(self):
        client = OllamaClient(base_url='http://localhost:19999')
        healthy = await client.health()
        assert healthy is False
        await client.close()
