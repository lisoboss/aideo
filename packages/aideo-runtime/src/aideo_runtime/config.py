"""Environment-backed Runtime configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Configuration required to run the HTTP Runtime service."""

    host: str
    port: int
    providers: list[str]

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
        )
