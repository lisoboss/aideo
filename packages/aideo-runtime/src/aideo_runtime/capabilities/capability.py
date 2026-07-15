"""Capability definitions."""

from enum import Enum


class Capability(str, Enum):
    """A provider-independent model capability."""

    CHAT = "chat"
    IMAGE = "image"
    VIDEO = "video"
    ASR = "asr"
    TTS = "tts"
    EMBEDDING = "embedding"
    VISION = "vision"
    RERANK = "rerank"
