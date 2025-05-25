import speech_recognition as sr
from .text_to_speech import speak

def listen(timeout=15, phrase_time_limit=60, max_retries=1):
    """
    Listen to the user's speech and convert it to text, handling various potential issues robustly
    while dynamically adapting to the noise environment.

    Parameters:
    - timeout: Maximum number of seconds that the function will wait for speech input.
    - phrase_time_limit: Maximum number of seconds allowed per phrase of speech.
    - max_retries: Number of times to attempt re-calibration and recognition if an UnknownValueError occurs.

    Returns:
    - A string containing the recognized text if successful, or None if recognition fails.
    """
    
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    # You can tune the damping to control how "quickly" it adapts to changes in volume
    recognizer.dynamic_energy_adjustment_damping = 0.15

    # A loop that can optionally retry if speech is not recognized the first time
    for attempt in range(max_retries + 1):
        # Attempt speech recognition within a try block
        try:
            with sr.Microphone() as source:
                print("\rListening", end='...', flush=True)
                # Initially calibrate for 1 second to quickly adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=1)

                try:
                    audio = recognizer.listen(
                        source, 
                        timeout=timeout, 
                        phrase_time_limit=phrase_time_limit
                    )
                    print("\rRecognizing", end='...', flush=True)
                    text = recognizer.recognize_google(audio)
                    if text:
                        print(f"\rUser: {text}", flush=True)
                        return text

                except sr.UnknownValueError:
                    # If we get here and have retries left, we do a short re-calibration 
                    # before trying again. This can help in a noisy environment.
                    if attempt < max_retries:
                        # A short re-calibration
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    else:
                        return None

                except sr.RequestError as e:
                    error_message = f"Apologies, there was an issue with the speech recognition service: {e}"
                    print(error_message)
                    speak(error_message)
                    return None

                except sr.WaitTimeoutError:
                    return None

                except Exception as e:
                    error_message = f"An unexpected error occurred during recognition: {e}"
                    print(error_message)
                    speak(error_message)
                    return None

        except OSError as e:
            error_message = f"Microphone not found or not accessible: {e}"
            print(error_message)
            speak(error_message)
            return None

        except Exception as e:
            error_message = f"An error occurred while trying to access the microphone: {e}"
            print(error_message)
            speak(error_message)
            return None

    return None
