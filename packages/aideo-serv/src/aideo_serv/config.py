"""Application settings for aideo-serv."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables with AIDEO_ prefix."""

    model_config = SettingsConfigDict(env_prefix="AIDEO_")

    server_host: str = "0.0.0.0"
    server_port: int = 8000
    runtime_url: str = "http://localhost:9090"
    storage_base_dir: str = "./data"
    cors_origins: list[str] = ["*"]

    # Paths passed to ltx2-service — aideo-serv is the source of truth
    model_root: str = "/mnt/g/AI/models"
    output_root: str = "./data/output"
    input_root: str = "./data/input"

    # Asset upload limits
    max_asset_size: int = 52428800  # 50 MB
    asset_base_dir: str = "./data/assets"

    # ------------------------------------------------------------------
    # AI provider settings
    # ------------------------------------------------------------------
    # Legacy single-provider mode:
    #   ai_provider: "stub" | "openai" | "runtime"
    #   ai_base_url / ai_api_key / ai_model for openai
    #
    # Multi-provider mode (preferred):
    #   ai_providers: JSON array of provider configs, e.g.:
    #   [{"name":"my-openai","type":"openai","base_url":"...","api_key":"...","model":"gpt-4o"}]
    ai_provider: str = "stub"
    ai_providers: str = ""  # JSON array, overrides ai_provider when set
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o"
