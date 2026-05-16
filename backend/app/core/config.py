from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./dev.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_eager_mode: bool = True  # For dev without Redis, set to False in production with Redis
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ]
    omium_api_key: str | None = None
    # Omium endpoint must be explicitly provided by the deployer (no default)
    omium_endpoint: str | None = None
    execute_workflows_sync: bool = False
    
    # Route specific agents to specific providers and models
    agent_providers: dict[str, str] = {}
    agent_models: dict[str, str] = {}
    
    # LLM provider integration
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5-coder"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4.1-mini"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    llm_request_timeout: float = 300.0  # 5 minutes for slow models like qwen2.5-coder
    llm_max_retries: int = 3  # Increase retries for network resilience
    llm_max_parallel_requests: int = 5
    qwen_temperature: float = 0.3
    qwen_max_new_tokens: int = 8192
    project_workspace_root: str = "./generated-workspaces"
    self_heal_max_retries: int = 2
    npm_install_command: str = "npm install"
    npm_build_command: str = "npm run build"
    npm_lint_command: str = "npm run lint"
    product_builder_llm_roles: list[str] = []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
