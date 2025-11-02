"""Text-to-speech utilities with online + offline backends.

Primary flow:
- If online, try StreamElements API and play via pygame with interrupt support.
- If that fails or offline, fall back to local pyttsx3 engine.
"""

import os
import pyttsx3
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")
import requests
import threading
from typing import Union, Optional
import tempfile
import uuid
from .system_control import is_connected

# Import interrupt handler
try:
    from .interrupt_handler import tts_interrupt_event
except ImportError:
    # Fallback if interrupt_handler doesn't exist yet
    tts_interrupt_event = threading.Event()

def generate_audio(message: str, voice: str = "Matthew") -> Union[None, bytes]:
    """
    Generate audio from text using the StreamElements API.

    :param message: Text message to convert to speech.
    :param voice: Voice to use for speech synthesis.
    :return: Audio content as bytes or None if the request fails.
    """
    # URL encode the message to handle spaces and special characters
    encoded_message = requests.utils.quote(message)
    url = f"https://api.streamelements.com/kappa/v2/speech?voice={voice}&text={encoded_message}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching audio from StreamElements API: {e}")
        return None

def play_audio_with_pygame(filepath: str) -> None:
    """
    Play audio file using pygame mixer with interrupt support.
    :param filepath: Path to the audio file.
    """
    # Import interrupt flag
    try:
        from .interrupt_handler import tts_interrupt_event
    except ImportError:
        import threading as _threading
        tts_interrupt_event = _threading.Event()

    # Lazy import pygame and fall back to playsound if unavailable
    try:
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
        import pygame  # type: ignore
        pygame.mixer.init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()

        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            if tts_interrupt_event.is_set():
                pygame.mixer.music.stop()
                break
            clock.tick(10)
    except Exception as e:
        try:
            from playsound import playsound  # type: ignore
            # playsound is blocking; check interrupt only before starting
            if not tts_interrupt_event.is_set():
                playsound(filepath)
        except Exception as e2:
            print(f"Audio playback failed (pygame error: {e}) and playsound fallback failed: {e2}")
    finally:
        try:
            # If pygame was imported, try to quit mixer
            if 'pygame' in globals():
                import pygame as _pg
                try:
                    _pg.mixer.quit()
                except Exception:
                    pass
        except Exception:
            pass

def speak_audio(message: str, voice: str = "Matthew", folder: Optional[str] = None, extension: str = ".mp3") -> Union[None, str]:
    """
    Save generated audio to a file, play it using pygame, and delete the file afterward.

    :param message: Text message to convert to speech.
    :param voice: Voice to use for speech synthesis.
    :param folder: Directory to save the audio file. Defaults to the current directory.
    :param extension: Extension for the audio file. Defaults to '.mp3'.
    :return: Path of the saved audio file or None if an error occurs.
    """
    # Use a writable temp directory and unique filename to avoid permission and collision issues
    folder = folder or tempfile.gettempdir()
    try:
        audio_content = generate_audio(message, voice)
        if audio_content is None:
            return None

        safe_name = f"jarvis_tts_{voice}_{uuid.uuid4().hex}{extension}"
        file_path = os.path.join(folder, safe_name)
        with open(file_path, "wb") as file:
            file.write(audio_content)

        try:
            # Use pygame for audio playback
            play_audio_with_pygame(file_path)
        except Exception as e:
            print(f"Error playing sound file '{file_path}': {e}")

        # Ensure playback has fully stopped before deletion; retry on PermissionError
        for attempt in range(3):
            try:
                os.remove(file_path)
                break
            except PermissionError:
                # Give mixer time to release the file handle
                import time as _time
                _time.sleep(0.15)
            except FileNotFoundError:
                break
        return file_path
    except Exception as e:
        print(f"Error in speak_audio function: {e}")
        return None

def speak(text: str) -> None:
    """
    Speak the given text using the appropriate method based on the system's connection status.

    :param text: Text to be spoken.
    """
    clean_text = text.strip()
    if is_connected():
        if not speak_audio(clean_text):
            # Fallback to local TTS if online synthesis fails
            print("Falling back to local TTS engine.")
            speak_tts(clean_text)
    else:
        speak_tts(clean_text)

def speak_tts(text: str) -> None:
    """
    Initialize the TTS engine, configure settings, and speak the given text.
    A fresh engine instance is created each time to avoid conflicts.
    """
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
        engine.setProperty('rate', 172)
        engine.setProperty('volume', 0.9)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Error during TTS speech synthesis: {e}")
