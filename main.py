import random, time
import hashlib, getpass
from modules.text_to_speech import speak
from modules.speech_recognition import listen, sr
from modules.system_control import is_connected
from modules.utils import greet, handle_query
from modules import password as PASSWORD

import logging

# --- Add Rich imports for modern interface ---
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()

# Disable all logging in the application
logging.disable(logging.CRITICAL)

# Hash the imported password 
STORED_PASSWORD_HASH = hashlib.sha256(PASSWORD.encode()).hexdigest()

def authenticate_user(attempts: int = 3):  # Allow three attempts
    """Authenticates the user by verifying the password."""
    console.print(Panel.fit("[bold cyan]Authentication Required[/bold cyan]", style="bold blue", box=box.ROUNDED))
    for _ in range(attempts):
        try:
            # Securely get the password without showing it in the console
            password = getpass.getpass("\nEnter password: ")
            if verify_password(password):
                console.print("[green]✔ Authentication successful. Access granted.[/green]")
                speak("Authentication successful.")
                return True
            else:
                console.print("[red]✖ Incorrect password. Try again.[/red]")
                speak("Incorrect password. Try again.")
                time.sleep(1.5)  # Pause to let the user see the message
        except KeyboardInterrupt:
            break

    console.print("[bold red]✖ Authentication failed. System locked.[/bold red]")
    speak("Authentication failed. System locked.")
    return False

def verify_password(password):
    """Verifies the entered password against the stored hash."""
    return hashlib.sha256(password.encode()).hexdigest() == STORED_PASSWORD_HASH

def get_greeting(online):
    """Generates a Jarvis-style greeting based on the online status."""
    greetings = [
        f"{greet()}! Jarvis at your service. All systems are green.",
        f"{greet()}! Operational and ready for your command.",
        f"{greet()}! Awaiting your instructions, sir.",
        f"{greet()}! Standing by to assist you with anything you need."
    ]

    online_status = random.choice([
        "Network connection verified. Full functionality enabled.",
        "Online and synchronized. Ready to execute your requests.",
        "Connected to all systems. Monitoring for your next command."
    ]) if online else random.choice([
        "Offline mode engaged. Some features may be restricted.",
        "No network detected. Operating with limited capabilities.",
        "Running in offline mode. Network-dependent tasks are unavailable."
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
            console.print(f"[cyan]{switch_message}[/cyan]")
            speak(switch_message)
            return 'voice'
        else:
            offline_message = random.choice([
                "Voice mode unavailable in offline mode. Reverting to text input.",
                "Cannot enable voice mode without an active connection.",
                "Offline status detected. Voice mode is inaccessible."
            ])
            console.print(f"[yellow]{offline_message}[/yellow]")
            speak(offline_message)
            return current_mode

    elif mode == "text mode":
        switch_message = random.choice([
            "Text mode activated. Ready for your input.",
            "Switching to text interface. Standing by.",
            "Text mode enabled. Awaiting your commands."
        ])
        console.print(f"[cyan]{switch_message}[/cyan]")
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
        console.print(f"[bold magenta]{farewell}[/bold magenta]")
        speak(farewell)
        return None

    handle_query(query, online)
    return mode

def main():
    """Main function that initializes the AI assistant and handles user interactions."""
    # --- Modern Rich Welcome Interface ---
    jarvis_title = Text("JARVIS AI ASSISTANT", style="bold white on blue", justify="center")
    subtitle = Text("Your Personal AI Assistant", style="italic cyan", justify="center")
    console.print(Panel(Align.center(jarvis_title), style="bold blue", box=box.DOUBLE, padding=(1, 4)))
    console.print(Align.center(subtitle))
    console.print("\n")

    if not authenticate_user():
        return  # Exit if authentication fails

    online = is_connected()
    greeting = get_greeting(online)

    # --- Modern separator and greeting ---
    separator = Text("─" * 80, style="dim")
    greeting_panel = Panel(
        Align.center(Text(greeting, style="bold green")),
        title="[bold blue]Welcome[/bold blue]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(separator)
    console.print(greeting_panel)
    console.print(separator)
    speak(greeting)

    mode = 'text' if not online else 'voice' # Just to start in text mode;  

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
            console.print(f"[yellow]{interrupt_message}[/yellow]")
            speak(interrupt_message)
            break

        except sr.UnknownValueError:
            error_message = random.choice([
                "I’m sorry, I didn’t catch that. Could you please repeat?",
                "My apologies, sir. I couldn’t understand that. Could you say it again?",
                "I'm afraid I missed that. Would you mind repeating?"
            ])
            console.print(f"[red]{error_message}[/red]")
            speak(error_message)

        except sr.RequestError as e:
            error_message = random.choice([
                f"Error connecting to speech recognition service: {e}. System functionality may be limited.",
                f"Speech recognition service unavailable: {e}. Please check your connection.",
                f"Speech recognition service failed: {e}. Awaiting further instructions."
            ])
            console.print(f"[red]{error_message}[/red]")
            speak(error_message)

        except Exception as e:
            error_message = random.choice([
                f"An unexpected error occurred: {e}. Attempting to recover.",
                f"System error detected: {e}. Please wait while I address this.",
                f"Critical error encountered: {e}. Implementing fail-safe protocols."
            ])
            console.print(f"[red]{error_message}[/red]")
            speak(error_message)

if __name__ == "__main__":
    main()
