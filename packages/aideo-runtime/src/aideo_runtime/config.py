"""Environment-backed Runtime configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from aideo_runtime.paths import PathSettings


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Configuration required to run the HTTP Runtime service."""

    host: str
    port: int
    providers: list[str]
    debug: bool = False
    paths: PathSettings = field(
        default_factory=lambda: PathSettings(
            Path("./models"), Path("./data/input"), Path("./data/output")
        )
    )

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        """Build settings from ``AIDEO_RUNTIME_*`` environment variables."""
        raw_providers = os.environ.get("AIDEO_RUNTIME_PROVIDERS", "demo")
        providers = [provider.strip() for provider in raw_providers.split(",")]
        if not all(providers):
            raise ValueError("AIDEO_RUNTIME_PROVIDERS contains an empty provider name")
        return cls(
            host=os.environ.get("AIDEO_RUNTIME_HOST", "127.0.0.1"),
            port=int(os.environ.get("AIDEO_RUNTIME_PORT", "9090")),
            providers=providers,
            debug=_bool_env("AIDEO_RUNTIME_DEBUG"),
            paths=PathSettings(
                Path(
                    os.environ.get(
                        "AIDEO_RUNTIME_MODELS_DIR",
                        os.environ.get("AIDEO_MODEL_ROOT", "./models"),
                    )
                ),
                Path(os.environ.get("AIDEO_RUNTIME_INPUT_DIR", "./data/input")),
                Path(os.environ.get("AIDEO_RUNTIME_OUTPUT_DIR", "./data/output")),
            ),
        )


def _bool_env(name: str) -> bool:
    """Parse an optional Runtime boolean environment variable."""
    raw_value = os.environ.get(name, "false").strip().lower()
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    if raw_value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")
