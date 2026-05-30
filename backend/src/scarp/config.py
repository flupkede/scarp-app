"""Scarp configuration — pydantic-settings with env var fallbacks."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = (
        Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "processed"
    )

    # LLM — provider-agnostic via OpenAI SDK
    llm_base_url: str = "https://api.deepinfra.com/v1/openai"
    llm_api_key: str = ""
    llm_model: str = "zai-org/GLM-4.7-Flash"

    # CORS — comma-separated in env, sane defaults
    cors_allow_origins: str = (
        "http://localhost:11001,http://localhost:4173,https://scarp.dsoft.services"
    )

    enable_search: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Pick up API key from any common env var if not explicitly set
if not settings.llm_api_key:
    settings.llm_api_key = (
        os.getenv("DEEPINFRA_API_KEY", "")
        or os.getenv("OPENAI_API_KEY", "")
        or os.getenv("ANTHROPIC_API_KEY", "")
    )

# Parse CORS origins from comma-separated string
CORS_ORIGINS = [
    origin.strip()
    for origin in settings.cors_allow_origins.split(",")
    if origin.strip()
]


def llm_provider_label() -> str:
    """Return a human-readable provider label based on base URL."""
    url = settings.llm_base_url.lower()
    if "deepinfra" in url:
        return "deepinfra"
    if "anthropic" in url:
        return "anthropic"
    if "openai" in url:
        return "openai"
    return "custom"
