"""Speech recognition utilities combining SpeechRecognition + Faster-Whisper.

Listens from microphone with animated status and transcribes using
faster-whisper. Integrates with interrupt flags to avoid conflicts
with keyboard-based TTS interruptions.
"""

import speech_recognition as sr
from .text_to_speech import speak
import time
import sys
import tempfile
import os
import torch
from faster_whisper import WhisperModel
import threading

# Import listening_active flag
try:
    from .interrupt_handler import listening_active
except ImportError:
    # Create fallback event if interrupt_handler doesn't exist
    listening_active = threading.Event()

# ---------------------------
# Global Whisper model (loaded once)
# ---------------------------
WHISPER_MODEL_SIZE = "base"  # change to "small", "medium", "large-v3" as needed
WHISPER_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_whisper_model = None
_whisper_lock = threading.Lock()

def _get_whisper_model():
    """Load Whisper model lazily to avoid startup cost when voice mode is unused."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            _whisper_model = WhisperModel(
                WHISPER_MODEL_SIZE,
                device=WHISPER_DEVICE,
                compute_type="float16" if WHISPER_DEVICE == "cuda" else "int8"
            )
    return _whisper_model

def animate_status(message, stop_event):
    """Threaded spinner animation for status updates in console."""
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {animation[idx % len(animation)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
    sys.stdout.flush()

def listen(timeout=15, phrase_time_limit=60, max_retries=2):
    """
    Listen to the user's speech and convert it to text, dynamically adapting to the noise environment
    for improved voice capture, with smooth animations for key statuses to enhance user flow.

    Parameters:
    - timeout: Maximum seconds to wait for speech input (default: 15).
    - phrase_time_limit: Maximum seconds allowed per phrase (default: 60).
    - max_retries: Number of retry attempts for recognition failures (default: 2).

    Returns:
    - Recognized text as a string if successful, or None if recognition fails.
    """
    # Signal that main listening is active
    listening_active.set()
    
    try:
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 300  # Initial energy threshold
        recognizer.dynamic_energy_adjustment_damping = 0.1  # Faster adaptation
        recognizer.dynamic_energy_ratio = 1.5  # Adjust sensitivity to voice vs. noise

        for attempt in range(max_retries + 1):
            try:
                with sr.Microphone() as source:
                    # Adjust for ambient noise dynamically
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)

                    # Start listening animation
                    stop_listen = threading.Event()
                    listen_thread = threading.Thread(target=animate_status, args=("Listening", stop_listen))
                    listen_thread.start()

                    try:
                        # Listen for audio input
                        audio = recognizer.listen(
                            source,
                            timeout=timeout,
                            phrase_time_limit=phrase_time_limit
                        )
                        stop_listen.set()
                        listen_thread.join()

                        # Start recognizing animation
                        stop_recognize = threading.Event()
                        recognize_thread = threading.Thread(target=animate_status, args=("Recognizing", stop_recognize))
                        recognize_thread.start()

                        # Transcribe audio using Faster-Whisper
                        temp_path = None
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                            temp_path = tf.name
                            tf.write(audio.get_wav_data())

                        try:
                            whisper_model = _get_whisper_model()
                            segments, _ = whisper_model.transcribe(temp_path, beam_size=7)  # Increased beam_size for better accuracy
                            text = " ".join([seg.text for seg in segments]).strip()
                        finally:
                            # Always stop spinner and clean up temp file
                            stop_recognize.set()
                            recognize_thread.join()
                            if temp_path and os.path.exists(temp_path):
                                try:
                                    os.remove(temp_path)
                                except Exception:
                                    pass

                        if text:
                            print(f"\rUser said: {text}")
                            return text

                    except sr.UnknownValueError:
                        stop_listen.set()
                        listen_thread.join()
                        if attempt < max_retries:
                            # Silently adjust for next attempt
                            recognizer.energy_threshold *= 1.2
                            recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        continue

                    except sr.WaitTimeoutError:
                        stop_listen.set()
                        listen_thread.join()
                        continue  # Retry silently on timeout

                    except sr.RequestError as e:
                        stop_listen.set()
                        listen_thread.join()
                        speak(f"Speech service error: {e}")
                        return None

                    except Exception as e:
                        stop_listen.set()
                        listen_thread.join()
                        speak(f"Recognition error: {e}")
                        return None

            except OSError as e:
                speak(f"Microphone error: {e}")
                return None

            except Exception as e:
                speak(f"Audio input error: {e}")
                return None

        return None
        
    finally:
        # Clear listening flag when done
        listening_active.clear()
