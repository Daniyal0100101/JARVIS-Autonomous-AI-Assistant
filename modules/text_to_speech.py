import pyttsx3
import pygame
import requests
import os
from typing import Union, Optional
from .system_control import is_connected

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

def play_audio_with_pygame(file_path: str) -> None:
    """
    Play an audio file using pygame.

    :param file_path: Path to the audio file to be played.
    """
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Wait until the audio finishes playing
    except Exception as e:
        print(f"Error playing audio with pygame: {e}")
    finally:
        pygame.mixer.quit()

def speak_audio(message: str, voice: str = "Matthew", folder: Optional[str] = None, extension: str = ".mp3") -> Union[None, str]:
    """
    Save generated audio to a file, play it using pygame, and delete the file afterward.

    :param message: Text message to convert to speech.
    :param voice: Voice to use for speech synthesis.
    :param folder: Directory to save the audio file. Defaults to the current directory.
    :param extension: Extension for the audio file. Defaults to '.mp3'.
    :return: Path of the saved audio file or None if an error occurs.
    """
    folder = folder or ""
    try:
        audio_content = generate_audio(message, voice)
        if audio_content is None:
            return None

        file_path = os.path.join(folder, f"{voice}{extension}")
        with open(file_path, "wb") as file:
            file.write(audio_content)

        try:
            # Use pygame for audio playback
            play_audio_with_pygame(file_path)
        except Exception as e:
            print(f"Error playing sound file '{file_path}': {e}")

        os.remove(file_path)
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
