import pytest

from agents import agent_server


@pytest.mark.asyncio
async def test_resolve_model_prefers_installed_requested(monkeypatch):
    async def fake_installed():
        return {'qwen2.5-coder:1.5b', 'nomic-embed-text'}

    monkeypatch.setattr(agent_server, 'installed_models', fake_installed)
    result = await agent_server.resolve_model('qwen2.5-coder:1.5b', 'qwen2.5-coder:1.5b')
    assert result == 'qwen2.5-coder:1.5b'


@pytest.mark.asyncio
async def test_resolve_model_falls_back_to_default_when_requested_missing(monkeypatch):
    async def fake_installed():
        return {'qwen2.5-coder:1.5b'}

    monkeypatch.setattr(agent_server, 'installed_models', fake_installed)
    result = await agent_server.resolve_model('deepseek-coder:1.3b', 'qwen2.5-coder:1.5b')
    assert result == 'qwen2.5-coder:1.5b'


@pytest.mark.asyncio
async def test_resolve_model_picks_installed_when_default_also_missing(monkeypatch):
    async def fake_installed():
        return {'some-other-model:latest'}

    monkeypatch.setattr(agent_server, 'installed_models', fake_installed)
    result = await agent_server.resolve_model('deepseek-coder:1.3b', 'missing-default:latest')
    assert result == 'some-other-model:latest'


@pytest.mark.asyncio
async def test_resolve_model_uses_first_candidate_when_none_installed(monkeypatch):
    async def fake_installed():
        return set()

    monkeypatch.setattr(agent_server, 'installed_models', fake_installed)
    result = await agent_server.resolve_model('deepseek-coder:1.3b', 'missing-default:latest')
    assert result == 'deepseek-coder:1.3b'