"""Application settings for aideo-serv."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables with AIDEO_ prefix."""

    model_config = SettingsConfigDict(env_prefix="AIDEO_")

    server_host: str = "0.0.0.0"
    server_port: int = 8000
    inference_url: str = "http://localhost:9090"
    storage_base_dir: str = "./data"
    cors_origins: list[str] = ["*"]
