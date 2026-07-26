import pytest
from unittest.mock import AsyncMock, patch
from agents.embedding_generator.generator import EmbeddingGenerator


class TestEmbeddingGenerator:
    @pytest.mark.asyncio
    async def test_empty_chunks(self):
        gen = EmbeddingGenerator()
        result = await gen.run([])
        assert result['status'] == 'ok'
        assert result['embeddings'] == []
        assert result['count'] == 0

    @pytest.mark.asyncio
    async def test_single_chunk(self):
        gen = EmbeddingGenerator()
        gen.ollama = AsyncMock()
        gen.ollama.embed.return_value = [[0.1, 0.2, 0.3]]
        result = await gen.run([{'content': 'hello'}])
        assert result['status'] == 'ok'
        assert result['count'] == 1
        assert len(result['embeddings']) == 1

    @pytest.mark.asyncio
    async def test_multiple_chunks(self):
        gen = EmbeddingGenerator()
        gen.ollama = AsyncMock()
        gen.ollama.embed.return_value = [[0.1], [0.2], [0.3]]
        result = await gen.run([{'content': 'a'}, {'content': 'b'}, {'content': 'c'}])
        assert result['count'] == 3
        assert result['failed'] == 0

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        gen = EmbeddingGenerator()
        gen.settings.batch_size = 2
        gen.ollama = AsyncMock()
        gen.ollama.embed.side_effect = [
            [[0.1], [0.2]],
            Exception('Ollama error'),
        ]
        result = await gen.run([{'content': 'a'}, {'content': 'b'}, {'content': 'c'}, {'content': 'd'}])
        assert result['status'] == 'partial'
        assert result['failed'] == 2

    @pytest.mark.asyncio
    async def test_fallback_text_field(self):
        gen = EmbeddingGenerator()
        gen.ollama = AsyncMock()
        gen.ollama.embed.return_value = [[0.1]]
        result = await gen.run([{'text': 'hello'}])
        assert result['status'] == 'ok'
        assert result['count'] == 1

    @pytest.mark.asyncio
    async def test_batch_respects_batch_size(self):
        gen = EmbeddingGenerator()
        gen.settings.batch_size = 2
        gen.ollama = AsyncMock()
        gen.ollama.embed.return_value = [[0.1], [0.2]]
        result = await gen.run([{'content': 'a'}, {'content': 'b'}, {'content': 'c'}, {'content': 'd'}])
        assert gen.ollama.embed.call_count == 2
        assert result['count'] == 4
