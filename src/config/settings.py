from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # OpenRouter (OpenAI-compatible proxy)
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    openai_model: str = Field(default="openai/gpt-4.1-mini", alias="OPENAI_MODEL")

    # Gemini (via OpenRouter)
    gemini_model: str = Field(default="google/gemini-3-flash-preview", alias="GEMINI_MODEL")

    # Tavily
    tavily_api_key: str = Field(..., alias="TAVILY_API_KEY")

    # Neo4j (Aura or local)
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(
        default="neo4j",
        validation_alias=AliasChoices("NEO4J_USER", "NEO4J_USERNAME"),
    )
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(
        default="neo4j",
        validation_alias=AliasChoices("NEO4J_DATABASE", "AURA_INSTANCEID"),
    )

    # LangSmith (accept LANGSMITH_* or LANGCHAIN_* env vars)
    langsmith_tracing: bool = Field(
        default=True,
        validation_alias=AliasChoices("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2"),
    )
    langsmith_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"),
    )
    langsmith_project: str = Field(
        default="deep-research-agent",
        validation_alias=AliasChoices("LANGSMITH_PROJECT", "LANGCHAIN_PROJECT"),
    )
    langsmith_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("LANGSMITH_ENDPOINT", "LANGCHAIN_ENDPOINT"),
    )

    # App
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_research_iterations: int = Field(default=5, alias="MAX_RESEARCH_ITERATIONS")
    confidence_threshold: float = Field(default=0.7, alias="CONFIDENCE_THRESHOLD")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
