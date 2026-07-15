"""Backend health models."""

from dataclasses import dataclass
from enum import Enum


class HealthStatus(str, Enum):
    """Result of a backend health probe."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class BackendState:
    """Mutable operational state tracked for a backend."""

    latency: float | None = None
    qps: float = 0.0
    running_jobs: int = 0
    max_jobs: int | None = None
    healthy: bool = False
