"""Tests for normalized request-level inference parameters."""

import pytest
from aideo_runtime.models.parameters import InferenceParameters


def test_parameters_normalize_supported_request_options() -> None:
    """Supported options should preserve their provider-neutral representation."""
    parameters = InferenceParameters.from_dict(
        {
            "max_output_tokens": 128,
            "temperature": 0.7,
            "top_p": 0.95,
            "stop": ["END"],
            "seed": 42,
            "reasoning_effort": "high",
            "truncation": "auto",
        }
    )

    assert parameters.max_output_tokens == 128
    assert parameters.stop == ("END",)
    assert parameters.to_dict()["truncation"] == "auto"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"max_output_tokens": 0}, "max_output_tokens"),
        ({"temperature": 2.1}, "temperature"),
        ({"top_p": 0}, "top_p"),
        ({"truncation": "invalid"}, "truncation"),
    ],
)
def test_parameters_reject_invalid_values(
    payload: dict[str, object], message: str
) -> None:
    """Invalid common parameter values should be rejected before a backend call."""
    with pytest.raises(ValueError, match=message):
        InferenceParameters.from_dict(payload)
