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
    base_greeting = f"{greet()}! Jarvis at your service."
    online_greetings = [
        "All systems are green.",
        "Operational and ready.",
        "Awaiting your instructions.",
        "Standing by to assist."
    ]
    offline_greetings = [
        "Operating in offline mode.",
        "Running with limited capabilities.",
        "Network connection unavailable."
    ]
    online_status = random.choice(online_greetings) if online else random.choice(offline_greetings)
    availability = "How may I assist you today?"
    return f"{base_greeting} {online_status} {availability}"

def switch_mode(query, current_mode, online):
    """Switches between voice and text mode based on user query."""
    mode = query.lower().split("switch to ")[-1].strip()

    if mode == "voice mode":
        if online:
            switch_messages = [
                "Activating voice mode.",
                "Voice mode enabled.",
                "Switching to voice interface."
            ]
            readiness = "Listening attentively."
            switch_message = f"{random.choice(switch_messages)} {readiness}"
            console.print(f"[cyan]{switch_message}[/cyan]")
            speak(switch_message)
            return 'voice'
        else:
            offline_messages = [
                "Voice mode unavailable in offline mode.",
                "Cannot enable voice mode without an active connection.",
                "Offline status detected. Voice mode is inaccessible."
            ]
            reversion = "Reverting to text input."
            offline_message = f"{random.choice(offline_messages)} {reversion}"
            console.print(f"[yellow]{offline_message}[/yellow]")
            speak(offline_message)
            return current_mode

    elif mode == "text mode":
        switch_messages = [
            "Text mode activated.",
            "Switching to text interface.",
            "Text mode enabled."
        ]
        readiness = "Ready for your input."
        switch_message = f"{random.choice(switch_messages)} {readiness}"
        console.print(f"[cyan]{switch_message}[/cyan]")
        speak(switch_message)
        return 'text'

    return current_mode

def get_farewell_message():
    """Generates a Jarvis-style farewell message."""
    farewell_messages = [
        "System shutdown initiated.",
        "Logging off.",
        "System deactivated.",
        "Goodbye, sir."
    ]
    awaiting = "Awaiting further instructions."
    return f"{random.choice(farewell_messages)} {awaiting}"

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
    title_text = Text("JARVIS AI ASSISTANT", style="bold white on blue")
    title_panel = Panel(
        Align.center(title_text),
        title="[bold blue]AI System[/bold blue]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2)
    )

    subtitle_text = Text("Your Personal AI Assistant", style="italic cyan", justify="center")
    
    console.print(title_panel)
    console.print(Align.center(subtitle_text))
    console.print("\n")

    if not authenticate_user():
        return  # Exit if authentication fails

    online = is_connected()
    
    # Initialize interrupt handler silently
    try:
        from modules.interrupt_handler import init_interrupt_handler, cleanup_interrupt_handler
        init_interrupt_handler()
    except ImportError:
        cleanup_interrupt_handler = None
    
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

    mode = 'text' if not online else 'voice'  # Just to start in text mode

    try:
        while True:
            try:
                query = listen() if mode == 'voice' else input("\nYou: ")
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
                    "I'm sorry, I didn't catch that. Could you please repeat?",
                    "My apologies, sir. I couldn't understand that. Could you say it again?",
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
    
    finally:
        # Cleanup interrupt handler
        if cleanup_interrupt_handler:
            cleanup_interrupt_handler()

if __name__ == "__main__":
    main()
