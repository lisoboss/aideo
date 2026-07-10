"""Tests for speech-to-text providers."""

import asyncio
import io
import wave

import pytest


# ---------------------------------------------------------------------------
# Helper — generate a minimal WAV file for testing
# ---------------------------------------------------------------------------


def _make_test_wav(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate a small WAV file containing silence."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        num_samples = int(duration_sec * sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Provider interface tests (no model download)
# ---------------------------------------------------------------------------


class TestFasterWhisperProvider:
    """Test FasterWhisperProvider interface compliance and lifecycle."""

    @pytest.fixture
    def provider(self):
        from aideo_runtime.speech.faster_whisper import FasterWhisperProvider

        return FasterWhisperProvider(model_size_or_path="tiny", device="cpu", compute_type="int8")

    def test_provider_name(self, provider):
        assert provider.provider_name == "faster-whisper"

    def test_not_loaded_initially(self, provider):
        assert provider.is_loaded is False

    def test_inherits_speech_provider(self, provider):
        from aideo_runtime.speech.provider import SpeechProvider

        assert isinstance(provider, SpeechProvider)

    def test_inherits_base_provider(self, provider):
        from aideo_runtime.provider import BaseProvider

        assert isinstance(provider, BaseProvider)

    def test_run_is_async_generator(self, provider):
        coro = provider.run(audio_path="/nonexistent.mp3")
        assert hasattr(coro, "__aiter__")

    @pytest.mark.asyncio
    async def test_run_with_missing_file_yields_error(self, provider):
        events = []
        async for event in provider.run(audio_path="/nonexistent/audio.mp3"):
            events.append(event)

        assert len(events) == 1
        assert "result_data" in events[0]
        assert "error" in events[0]["result_data"]


# ---------------------------------------------------------------------------
# Live test (requires model download ~75MB, run with --run-live)
# ---------------------------------------------------------------------------


class TestFasterWhisperProviderLive:
    """Integration tests with real faster-whisper model."""

    @pytest.fixture
    def provider(self):
        from aideo_runtime.speech.faster_whisper import FasterWhisperProvider

        return FasterWhisperProvider(model_size_or_path="tiny", device="cpu", compute_type="int8")

    @pytest.fixture
    def test_audio(self, tmp_path):
        """Create a tiny WAV file."""
        wav_bytes = _make_test_wav(duration_sec=1.0)
        path = tmp_path / "test.wav"
        path.write_bytes(wav_bytes)
        return str(path)

    @pytest.mark.asyncio
    async def test_load_and_transcribe(self, provider, test_audio):
        """End-to-end: load tiny model, transcribe silence."""
        events = []
        async for event in provider.run(audio_path=test_audio):
            events.append(event)

        # Last event should have result_data
        assert events[-1].get("result_data") is not None
        result = events[-1]["result_data"]
        assert "full_text" in result
        assert "language" in result
        assert "segments" in result
        assert "duration_seconds" in result

        # Model should now be loaded
        assert provider.is_loaded
