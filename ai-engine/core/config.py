from pydantic_settings import BaseSettings

class AgentSettings(BaseSettings):
    ollama_base_url: str = 'http://ollama:11434'
    embed_model: str = 'nomic-embed-text'
    llm_model: str = 'qwen2.5-coder:1.5b'
    rca_model: str = 'qwen2.5-coder:1.5b'
    batch_size: int = 32
    log_level: str = 'INFO'

    class Config:
        env_prefix = 'AGENT_'
