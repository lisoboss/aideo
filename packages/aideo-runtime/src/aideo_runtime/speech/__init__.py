"""Speech-to-text providers."""

from aideo_runtime.speech.provider import PROVIDERS, SpeechProvider, get_provider, register_provider

# Import implementations so they self-register via @register_provider
import aideo_runtime.speech.faster_whisper  # noqa: F401
