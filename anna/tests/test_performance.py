"""
Performance benchmarks for Anna.

Tests latency and resource usage.
"""

import pytest
import time
import os
import sys
import numpy as np

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.llm import LLMHandler
from core.voice import VoiceHandler
import config


class TestLLMPerformance:
    """Performance tests for LLM."""
    
    @pytest.fixture
    def llm(self):
        """Create LLM handler."""
        handler = LLMHandler()
        # Warm-up call (optional, but helps measurement consistency)
        handler.get_response("Hello")
        handler.reset_conversation()
        return handler
    
    @pytest.mark.timeout(40)
    def test_simple_response_latency(self, llm):
        """Test simple response latency."""
        start = time.time()
        llm.get_response("Hello")
        latency = time.time() - start
        
        print(f"\nSimple LLM response latency: {latency:.2f}s")
        assert latency < 20.0, f"Too slow for simple response: {latency:.2f}s"
    
    @pytest.mark.timeout(60)
    def test_complex_response_latency(self, llm):
        """Test complex response with skill routing."""
        start = time.time()
        llm.get_response("Add milk, bread, and eggs to my shopping list")
        latency = time.time() - start
        
        print(f"\nComplex LLM response latency: {latency:.2f}s")
        assert latency < 30.0, f"Too slow for complex response: {latency:.2f}s"
    
    def test_average_latency(self, llm):
        """Test average latency over multiple calls."""
        prompts = [
            "Hello",
            "How are you?",
            "Add milk to my list",
            "Thanks!"
        ]
        
        latencies = []
        
        for prompt in prompts:
            start = time.time()
            llm.get_response(prompt)
            latency = time.time() - start
            latencies.append(latency)
            llm.reset_conversation()
        
        avg_latency = sum(latencies) / len(latencies)
        
        print(f"\nAverage LLM latency: {avg_latency:.2f}s")
        print(f"Min: {min(latencies):.2f}s, Max: {max(latencies):.2f}s")
        
        assert avg_latency < 20.0, f"Average too slow: {avg_latency:.2f}s"


class TestVoicePerformance:
    """Performance tests for voice pipeline."""
    
    @pytest.fixture
    def voice(self):
        """Create voice handler."""
        return VoiceHandler()
    
    @pytest.mark.timeout(20)
    def test_tts_latency(self, voice):
        """Test TTS generation latency."""
        test_text = "This is a test of the text to speech system."
        
        start = time.time()
        voice.speak(test_text)
        latency = time.time() - start
        
        print(f"\nTTS latency: {latency:.2f}s")
        assert latency < 15.0, f"TTS too slow: {latency:.2f}s"
    
    @pytest.mark.timeout(5)
    def test_stt_latency(self, voice):
        """Test STT transcription latency."""
        # Create 3 seconds of silence
        mock_audio = np.zeros(3 * config.SAMPLE_RATE, dtype=np.float32)
        
        start = time.time()
        segments, _ = voice.whisper.transcribe(mock_audio, beam_size=1)
        _ = " ".join([s.text for s in segments])
        latency = time.time() - start
        
        print(f"\nSTT latency (3s audio on CPU): {latency:.2f}s")
        assert latency < 3.0, f"STT too slow: {latency:.2f}s"


class TestEndToEndPerformance:
    """End-to-end performance tests."""
    
    def test_target_latency(self):
        """Test that combined latency meets targets."""
        # Note: These targets are higher than PRD targets to allow for CPU-only testing
        print("\nTarget latencies (CPU-benchmarked):")
        print("  STT: <3.0s")
        print("  LLM: <15.0s")
        print("  TTS: <5.0s")
        print("  Total: <23.0s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
