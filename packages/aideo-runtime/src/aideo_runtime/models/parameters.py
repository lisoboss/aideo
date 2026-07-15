"""Provider-neutral request-level inference parameters."""

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class InferenceParameters:
    """Normalized generation controls supplied with an inference request."""

    max_output_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stop: tuple[str, ...] = ()
    seed: int | None = None
    reasoning_effort: str | None = None
    truncation: Literal["auto", "disabled"] = "disabled"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InferenceParameters":
        """Parse and validate recognized parameters from a request object."""
        max_output_tokens = data.get("max_output_tokens")
        temperature = data.get("temperature")
        top_p = data.get("top_p")
        stop = data.get("stop", [])
        truncation = data.get("truncation", "disabled")
        if max_output_tokens is not None and (
            not isinstance(max_output_tokens, int) or max_output_tokens < 1
        ):
            raise ValueError("max_output_tokens must be a positive integer")
        if temperature is not None and (
            not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2
        ):
            raise ValueError("temperature must be between 0 and 2")
        if top_p is not None and (
            not isinstance(top_p, (int, float)) or not 0 < top_p <= 1
        ):
            raise ValueError("top_p must be greater than 0 and at most 1")
        if not isinstance(stop, list) or not all(
            isinstance(item, str) for item in stop
        ):
            raise ValueError("stop must be a list of strings")
        if truncation not in {"auto", "disabled"}:
            raise ValueError("truncation must be auto or disabled")
        return cls(
            max_output_tokens=max_output_tokens,
            temperature=float(temperature) if temperature is not None else None,
            top_p=float(top_p) if top_p is not None else None,
            stop=tuple(stop),
            seed=data.get("seed"),
            reasoning_effort=data.get("reasoning_effort"),
            truncation=truncation,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return normalized parameters as a provider-ready mapping."""
        values: dict[str, Any] = {"truncation": self.truncation}
        for key in (
            "max_output_tokens",
            "temperature",
            "top_p",
            "seed",
            "reasoning_effort",
        ):
            value = getattr(self, key)
            if value is not None:
                values[key] = value
        if self.stop:
            values["stop"] = list(self.stop)
        return values
