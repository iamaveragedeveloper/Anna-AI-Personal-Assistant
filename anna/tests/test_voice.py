"""
Unit tests for Voice Handler.

Tests STT, TTS, and wake word detection without requiring voice input.
"""

import pytest
import numpy as np
from core.voice import VoiceHandler
import config


class TestVoiceHandler:
    """Test suite for VoiceHandler class."""
    
    @pytest.fixture
    def voice_handler(self):
        """Create voice handler instance for testing."""
        return VoiceHandler()
    
    def test_initialization(self, voice_handler):
        """Test that voice handler initializes correctly."""
        assert voice_handler is not None
        assert voice_handler.whisper is not None
        assert voice_handler.tts is not None
    
    def test_speak_method_exists(self, voice_handler):
        """Test that speak method exists and accepts text."""
        # Should not raise an exception
        voice_handler.speak("Test message")
    
    def test_empty_speak(self, voice_handler):
        """Test that empty text is handled gracefully."""
        # Should not crash
        voice_handler.speak("")
        voice_handler.speak("   ")
    
    def test_audio_devices_list(self, voice_handler):
        """Test that audio devices can be listed."""
        # Should not crash
        voice_handler.list_audio_devices()
    
    def test_transcription_with_mock_audio(self, voice_handler):
        """Test transcription with synthetic audio."""
        # Create 1 second of silence
        mock_audio = np.zeros(config.SAMPLE_RATE, dtype=np.float32)
        
        # Transcribe (should return empty or minimal text)
        segments, _ = voice_handler.whisper.transcribe(mock_audio, beam_size=1)
        text = " ".join([s.text for s in segments]).strip()
        
        # Empty audio should produce minimal/empty transcription
        assert len(text) < 50  # Should be short or empty


class TestVoiceConfiguration:
    """Test voice configuration settings."""
    
    def test_config_values_exist(self):
        """Test that all required config values are set."""
        assert hasattr(config, 'WAKE_WORD')
        assert hasattr(config, 'WHISPER_MODEL')
        assert hasattr(config, 'COQUI_MODEL')
        assert hasattr(config, 'SAMPLE_RATE')
        assert hasattr(config, 'SILENCE_THRESHOLD')
    
    def test_config_values_valid(self):
        """Test that config values are valid."""
        assert config.WAKE_WORD.lower() == "anna"
        assert config.SAMPLE_RATE == 16000
        assert 0 < config.SILENCE_THRESHOLD < 1
        assert config.SILENCE_DURATION > 0
        assert config.MAX_RECORDING_DURATION > 0


def test_voice_module_imports():
    """Test that voice module imports successfully."""
    from core import voice
    assert hasattr(voice, 'VoiceHandler')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
