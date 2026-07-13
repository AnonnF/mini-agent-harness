from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from mini_agent.exceptions import ConfigurationError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    request_timeout: float = 30.0
    max_agent_steps: int = 10


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigurationError(
            "Invalid or missing configuration. Check required environment variables."
        ) from exc
