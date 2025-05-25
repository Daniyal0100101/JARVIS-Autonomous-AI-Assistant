import random, time
import hashlib, getpass
from modules.text_to_speech import speak
from modules.speech_recognition import listen, sr
from modules.system_control import is_connected
from modules.utils import greet, handle_query
from modules import password as stored_password
import logging

# Disable all logging in the application
logging.disable(logging.CRITICAL)

# Hash the imported password
STORED_PASSWORD_HASH = hashlib.sha256(stored_password.encode()).hexdigest()

def authenticate_user(attempts: int = 3):  # Allow three attempts
    """Authenticates the user by verifying the password."""
    print("Authentication Required.")
    for _ in range(attempts):
        try:
            # Securely get the password without showing it in the console
            password = getpass.getpass("\nEnter password: ")
            if verify_password(password):
                print("\rAuthentication successful. Access granted.")
                speak("Authentication successful.")
                return True
            else:
                print("\rIncorrect password. Try again.")
                speak("Incorrect password. Try again.")
                time.sleep(1.5)  # Pause to let the user see the message
        except KeyboardInterrupt:
            break

    print("\rAuthentication failed. System locked.")
    speak("Authentication failed. System locked.")
    return False

def verify_password(password):
    """Verifies the entered password against the stored hash."""
    return hashlib.sha256(password.encode()).hexdigest() == STORED_PASSWORD_HASH

def get_greeting(online):
    """Generates a greeting based on the online status."""
    greetings = [
        f"{greet()}! Systems are fully operational.",
        f"{greet()}! All systems online and at your disposal.",
        f"{greet()}! Standing by for your instructions.",
        f"{greet()}! Ready to assist you."
    ]

    online_status = random.choice([
        "Network connection established. Awaiting your command.",
        "Connected to the network. Ready to serve.",
        "Monitoring systems and awaiting your input."
    ]) if online else random.choice([
        "Operating in offline mode. Certain functions may be limited.",
        "No network detected. Running in offline mode.",
        "Offline mode active. Network-dependent features unavailable."
    ])

    return f"{random.choice(greetings)} {online_status} How may I assist you today?"

def switch_mode(query, current_mode, online):
    """Switches between voice and text mode based on user query."""
    mode = query.lower().split("switch to ")[-1].strip()

    if mode == "voice mode":
        if online:
            switch_message = random.choice([
                "Activating voice mode. Listening attentively.",
                "Voice mode enabled. Awaiting your verbal command.",
                "Switching to voice interface. Standing by."
            ])
            print(switch_message)
            speak(switch_message)
            return 'voice'
        else:
            offline_message = random.choice([
                "Voice mode unavailable in offline mode. Reverting to text input.",
                "Cannot enable voice mode without an active connection.",
                "Offline status detected. Voice mode is inaccessible."
            ])
            print(offline_message)
            speak(offline_message)
            return current_mode

    elif mode == "text mode":
        switch_message = random.choice([
            "Text mode activated. Ready for your input.",
            "Switching to text interface. Standing by.",
            "Text mode enabled. Awaiting your commands."
        ])
        print(switch_message)
        speak(switch_message)
        return 'text'

    return current_mode

def get_farewell_message():
    """Generates a Jarvis-style farewell message."""
    return random.choice([
        "System shutdown initiated. Goodbye, sir.",
        "Logging off. Awaiting further instructions.",
        "System deactivated. I will be here when you need me.",
        "Goodbye, sir. Standing by for your next command."
    ])

def handle_query_input(query, mode, online):
    """Processes the user's query and determines the mode or exit."""
    query_lower = query.lower()

    if "switch to" in query_lower:
        return switch_mode(query, mode, online)

    if any(keyword in query_lower for keyword in ['exit', 'break', 'quit', 'stop', 'bye', 'goodbye']):
        farewell = get_farewell_message()
        print(farewell)
        speak(farewell)
        return None

    handle_query(query, online)
    return mode

def main():
    """Main function that initializes the AI assistant and handles user interactions."""
    if not authenticate_user():
        return  # Exit if authentication fails

    online = is_connected()
    greeting = get_greeting(online)

    separator = "─" * 130
    print(f"\n{separator}\n{greeting}\n{separator}\n")
    speak(greeting)

    mode = 'text' if not online else 'voice'

    while True:
        try:
            query = listen() if mode == 'voice' else input("You: ")
            if query:
                mode = handle_query_input(query, mode, online)
                if mode is None:
                    break

        except KeyboardInterrupt:
            interrupt_message = random.choice([
                "\nUser interruption detected. Exiting the system.",
                "\nSession terminated by user command. Logging off.",
                "\nManual override acknowledged. Shutting down operations."
            ])
            print(interrupt_message)
            speak(interrupt_message)
            break

        except sr.UnknownValueError:
            error_message = random.choice([
                "I’m sorry, I didn’t catch that. Could you please repeat?",
                "My apologies, sir. I couldn’t understand that. Could you say it again?",
                "I'm afraid I missed that. Would you mind repeating?"
            ])
            print(error_message)
            speak(error_message)

        except sr.RequestError as e:
            error_message = random.choice([
                f"Error connecting to speech recognition service: {e}. System functionality may be limited.",
                f"Speech recognition service unavailable: {e}. Please check your connection.",
                f"Speech recognition service failed: {e}. Awaiting further instructions."
            ])
            print(error_message)
            speak(error_message)

        except Exception as e:
            error_message = random.choice([
                f"An unexpected error occurred: {e}. Attempting to recover.",
                f"System error detected: {e}. Please wait while I address this.",
                f"Critical error encountered: {e}. Implementing fail-safe protocols."
            ])
            print(error_message)
            speak(error_message)

if __name__ == "__main__":
    main()
