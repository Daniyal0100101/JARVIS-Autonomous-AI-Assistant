import speech_recognition as sr
from .text_to_speech import speak
import time
import sys
import tempfile
import torch
from faster_whisper import WhisperModel

# ---------------------------
# Global Whisper model (loaded once)
# ---------------------------
WHISPER_MODEL_SIZE = "small"  # change to "base", "medium", "large-v3" as needed
WHISPER_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load the Whisper model once
whisper_model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device=WHISPER_DEVICE,
    compute_type="float16" if WHISPER_DEVICE == "cuda" else "int8"
)

def animate_listening():
    """Animated listening indicator using carriage return."""
    animation = "|/-\\"
    idx = 0
    while True:
        sys.stdout.write(f"\rListening {animation[idx % len(animation)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
        yield

def listen(timeout=15, phrase_time_limit=60, max_retries=1):
    """
    Listen to the user's speech and convert it to text, handling various potential issues robustly
    while dynamically adapting to the noise environment with animated feedback.

    Parameters:
    - timeout: Maximum number of seconds that the function will wait for speech input
    - phrase_time_limit: Maximum number of seconds allowed per phrase of speech  
    - max_retries: Number of times to attempt re-calibration and recognition if recognition fails

    Returns:
    - A string containing the recognized text if successful, or None if recognition fails
    """
    
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15

    for attempt in range(max_retries + 1):
        try:
            with sr.Microphone() as source:
                # Start animated listening indicator
                animation_gen = animate_listening()
                next(animation_gen)
                
                print("\r", end='', flush=True)  # Clear any previous output
                recognizer.adjust_for_ambient_noise(source, duration=1)

                try:
                    # Listen with animation running
                    audio = recognizer.listen(
                        source, 
                        timeout=timeout, 
                        phrase_time_limit=phrase_time_limit
                    )
                    
                    # Stop animation and show recognition status
                    print("\r" + " " * 20 + "\r", end='', flush=True)  # Clear animation
                    print("Recognizing", end=" ", flush=True)

                    # --- Faster-Whisper transcription ---
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                        tf.write(audio.get_wav_data())  # write SR audio to temp wav
                        temp_path = tf.name

                    segments, _ = whisper_model.transcribe(temp_path, beam_size=5)
                    text = " ".join([seg.text for seg in segments]).strip()

                    if text:
                        print(f"\rUser said: {text}")
                        return text

                except sr.UnknownValueError:
                    # Clear animation on failure
                    print("\r" + " " * 20 + "\r", end='', flush=True)
                    if attempt < max_retries:
                        print("Adjusting for ambient noise", end=" ", flush=True)
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        print("Ready")
                    else:
                        print("No speech detected")
                        return None

                except sr.RequestError as e:
                    print("\r" + " " * 20 + "\r", end='', flush=True)
                    error_message = f"Speech service error: {e}"
                    print(error_message)
                    speak(error_message)
                    return None

                except sr.WaitTimeoutError:
                    print("\r" + " " * 20 + "\r", end='', flush=True)
                    print("Listening timeout")
                    return None

                except Exception as e:
                    print("\r" + " " * 20 + "\r", end='', flush=True)
                    error_message = f"Recognition error: {e}"
                    print(error_message)
                    speak(error_message)
                    return None

        except OSError as e:
            error_message = f"Microphone error: {e}"
            print(error_message)
            speak(error_message)
            return None

        except Exception as e:
            error_message = f"Audio input error: {e}"
            print(error_message)
            speak(error_message)
            return None

    return None
