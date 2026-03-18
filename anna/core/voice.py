"""
Voice Handler for Anna - manages STT, TTS, and wake word detection.

This module handles all voice-related operations:
- Wake word detection using continuous Whisper monitoring
- Speech-to-text transcription with faster-whisper
- Text-to-speech synthesis with Coqui TTS
"""

import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from TTS.api import TTS
import tempfile
import os
import time
from typing import Optional
import sys

# Add the parent directory to sys.path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class VoiceHandler:
    """
    Handles all voice input/output operations for Anna.
    
    Components:
    - Wake word detection (continuous listening)
    - Speech-to-text (faster-whisper)
    - Text-to-speech (Coqui TTS)
    """
    
    def __init__(self):
        """Initialize voice handler with STT and TTS models."""
        print("=" * 60)
        print("[INIT] Initializing Voice Handler...")
        print("=" * 60)
        
        # Initialize faster-whisper for STT
        print(f"\n[LOAD] Loading Whisper model: {config.WHISPER_MODEL}")
        print(f"   Device: {config.WHISPER_DEVICE}")
        
        self.whisper = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
            download_root=None  # Use default cache
        )
        print("   [INFO] Whisper loaded")
        
        # Initialize Coqui TTS
        print(f"\n[LOAD] Loading TTS model: {config.COQUI_MODEL}")
        print(f"   Device: {config.COQUI_DEVICE}")
        print("   (First run may download model - this can take a few minutes)")
        
        self.tts = TTS(
            model_name=config.COQUI_MODEL,
            progress_bar=False,
            gpu=(config.COQUI_DEVICE == "cuda")
        )
        print("   [INFO] TTS loaded")
        
        print("\n" + "=" * 60)
        print("[READY] Voice Handler ready!")
        print("=" * 60 + "\n")
    
    def listen_for_wake_word(self, timeout: float = 30.0) -> bool:
        """
        Continuously listen for wake word in audio chunks.
        
        Args:
            timeout: Maximum time to listen before giving up (seconds)
        
        Returns:
            True if wake word detected, False if timeout
        """
        print(f"[LISTEN] Listening for '{config.WAKE_WORD}'...", end="", flush=True)
        
        elapsed = 0.0
        chunk_samples = int(config.CHUNK_DURATION * config.SAMPLE_RATE)
        
        while elapsed < timeout:
            # Record audio chunk
            audio_chunk = sd.rec(
                chunk_samples,
                samplerate=config.SAMPLE_RATE,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            # Flatten to 1D array for Whisper
            audio_chunk = audio_chunk.flatten()
            
            # Quick transcription (beam_size=1 for speed)
            segments, _ = self.whisper.transcribe(
                audio_chunk,
                beam_size=1,
                language="en"
            )
            
            # Check if wake word is in transcription
            text = " ".join([segment.text for segment in segments]).strip().lower()
            
            if config.WAKE_WORD.lower() in text:
                print(f"\r[FOUND] Wake word '{config.WAKE_WORD}' detected!          ")
                return True
            
            elapsed += config.CHUNK_DURATION
            
            # Print progress dots every 3 seconds
            if int(elapsed) % 3 == 0:
                print(".", end="", flush=True)
        
        print(f"\r[TIMEOUT] Timeout after {timeout}s - no wake word detected")
        return False
    
    def listen_until_silence(self, max_duration: float = None) -> str:
        """
        Record audio until silence is detected or max duration reached.
        
        Args:
            max_duration: Maximum recording duration (uses config default if None)
        
        Returns:
            Transcribed text from the recording
        """
        if max_duration is None:
            max_duration = config.MAX_RECORDING_DURATION
        
        print("[LISTEN] Listening... (speak now, I'll detect when you stop)")
        
        chunks = []
        silence_chunks = 0
        chunk_samples = int(1.0 * config.SAMPLE_RATE)  # 1-second chunks
        max_silence_chunks = int(config.SILENCE_DURATION / 1.0)
        
        elapsed = 0.0
        
        while elapsed < max_duration:
            # Record chunk
            chunk = sd.rec(
                chunk_samples,
                samplerate=config.SAMPLE_RATE,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            # Check if chunk is silent
            chunk_amplitude = np.abs(chunk).mean()
            
            if chunk_amplitude < config.SILENCE_THRESHOLD:
                silence_chunks += 1
            else:
                silence_chunks = 0  # Reset on speech
            
            chunks.append(chunk)
            elapsed += 1.0
            
            # Stop if we've detected silence for long enough
            # (but only if we've recorded at least 1 second)
            if silence_chunks >= max_silence_chunks and len(chunks) > 1:
                print(f"   Silence detected after {elapsed:.1f}s")
                break
        
        if elapsed >= max_duration:
            print(f"   Max duration ({max_duration}s) reached")
        
        # Combine all chunks
        audio_data = np.concatenate(chunks).flatten()
        
        # Transcribe with higher quality (beam_size=5)
        print("[PROCESS] Transcribing...")
        segments, info = self.whisper.transcribe(
            audio_data,
            beam_size=5,
            language="en"
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        
        if text:
            print(f"   Heard: \"{text}\"")
        else:
            print("   (No speech detected)")
        
        return text
    
    def speak(self, text: str, speed: float = 1.0) -> None:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            speed: Speech speed multiplier (1.0 = normal, 1.1 = slightly faster)
        """
        if not text.strip():
            print("[WARN] No text to speak")
            return
        
        print(f"[SPEAK] Anna: {text}")
        
        try:
            # Generate speech to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Workaround for Windows file permission issues
            tmp_file.close()
            
            # Generate audio with Coqui TTS
            self.tts.tts_to_file(
                text=text,
                file_path=tmp_path,
                speed=speed
            )
            
            # Load and play audio
            audio_data, sample_rate = sf.read(tmp_path)
            
            sd.play(audio_data, sample_rate)
            sd.wait()  # Wait until playback finishes
            
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
        except Exception as e:
            print(f"[ERROR] TTS Error: {e}")
            print(f"   (Text would have been: {text})")
    
    def test_microphone(self) -> bool:
        """
        Test microphone input by recording and playing back 3 seconds.
        
        Returns:
            True if microphone works, False otherwise
        """
        print("\n[TEST] Testing microphone...")
        print("   Recording 3 seconds...")
        
        try:
            # Record 3 seconds
            duration = 3
            audio = sd.rec(
                int(duration * config.SAMPLE_RATE),
                samplerate=config.SAMPLE_RATE,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            # Check if we got any audio
            if np.abs(audio).max() < 0.001:
                print("   [FAIL] No audio detected - check microphone connection")
                return False
            
            print(f"   [OK] Audio recorded (peak: {np.abs(audio).max():.3f})")
            print("   Playing back...")
            
            # Play back
            sd.play(audio, config.SAMPLE_RATE)
            sd.wait()
            
            print("   [PASS] Microphone test passed!")
            return True
            
        except Exception as e:
            print(f"   [FAIL] Microphone test failed: {e}")
            return False
    
    def list_audio_devices(self):
        """Print available audio input devices."""
        print("\n[INFO] Available audio devices:")
        print(sd.query_devices())


# Standalone test function
def test_voice_pipeline():
    """
    Test the complete voice pipeline independently.
    This is the acceptance test for PRD 1.
    """
    print("\n" + "=" * 60)
    print("TESTING VOICE PIPELINE (PRD 1 ACCEPTANCE TEST)")
    print("=" * 60 + "\n")
    
    # Initialize voice handler
    voice = VoiceHandler()
    
    # Test 1: Microphone
    print("\n--- Test 1: Microphone ---")
    if not voice.test_microphone():
        print("\n[FAIL] FAILED: Microphone not working")
        return False
    
    # Test 2: TTS
    print("\n--- Test 2: Text-to-Speech ---")
    voice.speak("Hello! I'm Anna. Testing text to speech.")
    
    # Test 3: Wake word detection
    print("\n--- Test 3: Wake Word Detection ---")
    print(f"Say '{config.WAKE_WORD}' within 15 seconds...")
    
    if voice.listen_for_wake_word(timeout=15.0):
        voice.speak("Wake word detected successfully!")
    else:
        print("\n[WARN] Wake word not detected - try again or adjust microphone")
        return False
    
    # Test 4: Full voice loop
    print("\n--- Test 4: Full Voice Loop ---")
    print("Testing complete pipeline...")
    
    # Wait for wake word
    if voice.listen_for_wake_word(timeout=20.0):
        voice.speak("Yes? What do you need?")
        
        # Listen for command
        user_input = voice.listen_until_silence()
        
        if user_input:
            # Echo back what was heard
            voice.speak(f"I heard you say: {user_input}")
            
            print("\n" + "=" * 60)
            print("[PASS] ALL TESTS PASSED - Voice pipeline working!")
            print("=" * 60 + "\n")
            return True
        else:
            print("\n[WARN] No speech detected")
            return False
    else:
        print("\n[WARN] Wake word not detected")
        return False


if __name__ == "__main__":
    """
    Run this file directly to test the voice pipeline:
    python core/voice.py
    """
    test_voice_pipeline()
