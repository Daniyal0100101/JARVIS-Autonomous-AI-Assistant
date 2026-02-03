"""Entry point for the Jarvis AI Assistant.

This module wires together authentication, connection checks, the voice/text
interaction loop, and a modern terminal UI using Rich. It delegates concrete
actions to modules under `modules/` to keep concerns separated.
"""

import random
import time
import hashlib
import getpass
import os
import sys

# Cross-platform getch/getwch implementation
try:
    import msvcrt
    def getch():
        return msvcrt.getch()
    def getwch():
        return msvcrt.getwch()
except ImportError:
    # Fallback for non-Windows platforms
    try:
        import readchar
        def getch():
            return readchar.readchar().encode('utf-8')
        def getwch():
            return readchar.readchar()
    except ImportError:
        import tty
        import termios
        def getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                # Handle ANSI escape sequences for arrow keys
                if ch == '\x1b':  # ESC character
                    # Read the next two characters to complete the sequence
                    seq = ch + sys.stdin.read(2)
                    return seq.encode('utf-8')
                return ch.encode('utf-8')
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        def getwch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                # Handle ANSI escape sequences for arrow keys
                if ch == '\x1b':  # ESC character
                    # Read the next two characters to complete the sequence
                    seq = ch + sys.stdin.read(2)
                    return seq
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
from modules.text_to_speech import speak
from modules.speech_recognition import listen, sr
from modules.system_control import is_connected
from modules.utils import (
    greet,
    handle_query,
    clear_conversation_history,
    start_schedule_runner,
    stop_schedule_runner,
)
from modules import password as PASSWORD
from modules.task_daemon import initialize_daemon, shutdown_daemon

import logging

# --- Add Rich imports for modern interface ---
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()

def clear_console():
    """Clear the terminal to prevent duplicated panels on mode selection."""
    console.clear()
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

SLASH_COMMANDS = {
    "/help": "Show available slash commands",
    "/clear": "Clear chat history and console",
    "/model": "Show current provider (hosted/local)",
    "/status": "Show connection status and mode",
    "/exit": "Exit the assistant",
}
SLASH_COMMAND_LIST = list(SLASH_COMMANDS.keys())

def _get_slash_suggestions(buffer: str):
    if not buffer.startswith("/"):
        return []
    prefix = buffer.lower()
    return [cmd for cmd in SLASH_COMMAND_LIST if cmd.startswith(prefix)]

def _render_input(prompt: str, buffer: str, suggestions, selected_index: int, last_count: int) -> int:
    if last_count:
        sys.stdout.write(f"\x1b[{last_count}A")
        sys.stdout.write("\x1b[J")
    sys.stdout.write("\r\x1b[2K" + prompt + buffer)

    if suggestions:
        for idx, cmd in enumerate(suggestions):
            marker = ">" if idx == selected_index else " "
            desc = SLASH_COMMANDS.get(cmd, "")
            line = f"{marker} {cmd} - {desc}" if desc else f"{marker} {cmd}"
            sys.stdout.write("\n" + line)
        sys.stdout.write(f"\x1b[{len(suggestions)}A")
        sys.stdout.write("\r")
        sys.stdout.write(f"\x1b[{len(prompt) + len(buffer)}C")

    sys.stdout.flush()
    return len(suggestions)

def _finalize_input(prompt: str, buffer: str, last_count: int) -> None:
    if last_count:
        sys.stdout.write(f"\x1b[{last_count}A")
        sys.stdout.write("\x1b[J")
    sys.stdout.write("\r\x1b[2K" + prompt + buffer + "\n")
    sys.stdout.flush()

# Disable all logging in the application
logging.disable(logging.CRITICAL)

# Hash the imported password (avoid storing plain text in memory longer than needed)
STORED_PASSWORD_HASH = hashlib.sha256(PASSWORD.password.encode()).hexdigest()

def authenticate_user(attempts: int = 3):  # Allow three attempts
    """Prompt for a password and check against the stored hash."""
    console.print(Panel.fit("[bold cyan]Authentication Required[/bold cyan]", style="bold blue", box=box.ROUNDED))
    for _ in range(attempts):
        try:
            # Securely get the password without showing it in the console
            password = getpass.getpass("\nEnter password: ")
            if verify_password(password):
                console.print("[green]Authentication successful. Access granted.[/green]")
                speak("Authentication successful.")
                return True
            else:
                console.print("[red]Incorrect password. Try again.[/red]")
                speak("Incorrect password. Try again.")
                time.sleep(1.5)  # Pause to let the user see the message
        except KeyboardInterrupt:
            break

    console.print("[bold red]Authentication failed. System locked.[/bold red]")
    speak("Authentication failed. System locked.")
    return False

def verify_password(password):
    """Verify an entered password against the stored hash."""
    return hashlib.sha256(password.encode()).hexdigest() == STORED_PASSWORD_HASH

def get_greeting(online):
    """Generate a Jarvis-style greeting based on connectivity."""
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
    """Switch between voice and text modes based on user request."""
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
    """Generate a Jarvis-style farewell message."""
    farewell_messages = [
        "System shutdown initiated.",
        "Logging off.",
        "System deactivated.",
        "Goodbye, sir."
    ]
    awaiting = "Awaiting further instructions."
    return f"{random.choice(farewell_messages)} {awaiting}"

def select_start_mode(online):
    """Prompt the user to select the startup mode using arrow keys."""
    options = ["Voice Mode", "Text Mode"]
    selected_index = 0 if online else 1
    instructions = "Use Up/Down arrows, then press Enter."
    min_width = 40
    min_height = 8

    width = console.size.width
    height = console.size.height
    if width < min_width or height < min_height:
        prompt = "Select mode: [V]oice / [T]ext (or Q/quit/Enter to cancel): "
        while True:
            try:
                choice = input(prompt).strip().lower()
                if choice in {"q", "quit", ""}:
                    console.print("[yellow]Mode selection cancelled.[/yellow]")
                    return None
                if choice in {"v", "voice"}:
                    return "voice" if online else "text"
                if choice in {"t", "text"}:
                    return "text"
                console.print("[red]Invalid choice. Please try again.[/red]")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Mode selection cancelled.[/yellow]")
                return None
    while True:
        clear_console()
        console.print(Panel.fit("[bold cyan]Select Startup Mode[/bold cyan]", box=box.ROUNDED))
        console.print(f"[dim]{instructions}[/dim]\n")

        for index, label in enumerate(options):
            if index == selected_index:
                console.print(f"[bold green]> {label}[/bold green]")
            else:
                console.print(f"  {label}")

        key = getch()
        if key == b"\r":
            chosen = "voice" if selected_index == 0 else "text"
            if chosen == "voice" and not online:
                console.print("[yellow]Voice mode requires an online connection. Defaulting to text mode.[/yellow]")
                speak("Voice mode requires an online connection. Defaulting to text mode.")
                time.sleep(0.8)
                clear_console()
                return "text"
            clear_console()
            return chosen
        elif key in (b"q", b"Q"):
            console.print("[yellow]Mode selection cancelled.[/yellow]")
            clear_console()
            return None

        # Handle arrow keys (both Windows and ANSI escape sequences)
        if key in (b"\x00", b"\xe0"):
            # Windows-style arrow keys
            arrow_key = getch()
            if arrow_key == b"H":  # Up arrow
                selected_index = (selected_index - 1) % len(options)
            elif arrow_key == b"P":  # Down arrow
                selected_index = (selected_index + 1) % len(options)
        elif key.startswith(b"\x1b["):
            # ANSI escape sequences for arrow keys
            if key == b"\x1b[A":  # Up arrow
                selected_index = (selected_index - 1) % len(options)
            elif key == b"\x1b[B":  # Down arrow
                selected_index = (selected_index + 1) % len(options)

def prompt_user_input():
    """Render a cleaner input prompt for text mode."""
    min_width = 50
    min_height = 8

    width = console.size.width
    height = console.size.height
    if width < min_width or height < min_height:
        return input("\nYou > ")

    prompt = "You > "
    buffer = ""
    last_count = 0
    selected_index = 0

    sys.stdout.write(prompt)
    sys.stdout.flush()

    while True:
        char = getwch()

        if char in ("\r", "\n"):
            _finalize_input(prompt, buffer, last_count)
            return buffer.strip()
        if char == "\t":
            suggestions = _get_slash_suggestions(buffer)
            if suggestions:
                buffer = suggestions[selected_index]
        elif char in ("\x08", "\x7f"):
            buffer = buffer[:-1]
        elif char in ("\x03",):
            raise KeyboardInterrupt
        elif char in ("\x00", "\xe0"):
            # Windows-style arrow keys
            arrow = getwch()
            if arrow in ("H", "P"):
                suggestions = _get_slash_suggestions(buffer)
                if suggestions:
                    if arrow == "H":  # Up arrow
                        selected_index = (selected_index - 1) % len(suggestions)
                    else:  # Down arrow
                        selected_index = (selected_index + 1) % len(suggestions)
            continue
        elif char.startswith("\x1b["):
            # ANSI escape sequences for arrow keys
            if char == "\x1b[A" or char == "\x1bOA":  # Up arrow
                suggestions = _get_slash_suggestions(buffer)
                if suggestions:
                    selected_index = (selected_index - 1) % len(suggestions)
            elif char == "\x1b[B" or char == "\x1bOB":  # Down arrow
                suggestions = _get_slash_suggestions(buffer)
                if suggestions:
                    selected_index = (selected_index + 1) % len(suggestions)
            continue
        else:
            if char.isprintable():
                buffer += char

        suggestions = _get_slash_suggestions(buffer)
        if suggestions:
            selected_index = min(selected_index, len(suggestions) - 1)
        else:
            selected_index = 0

        last_count = _render_input(prompt, buffer, suggestions, selected_index, last_count)

def handle_slash_command(query: str, mode: str, online: bool):
    if not query.startswith("/"):
        return None

    command = query.strip().split()[0].lower()
    if command == "/help":
        message = "Available commands: " + ", ".join(SLASH_COMMAND_LIST)
    elif command == "/clear":
        clear_conversation_history()
        clear_console()
        message = "Chat history cleared."
    elif command == "/model":
        provider = "Hosted (Gemini)" if online else "Local (Ollama)"
        message = f"Current provider: {provider}."
    elif command == "/status":
        connection = "Online" if is_connected() else "Offline"
        message = f"Status: {connection}. Mode: {mode}."
    elif command == "/exit":
        farewell = get_farewell_message()
        console.print(f"[bold magenta]{farewell}[/bold magenta]")
        speak(farewell)
        return None
    else:
        message = "Unknown command. Type /help to see available commands."

    console.print(f"[cyan]{message}[/cyan]")
    speak(message)
    return mode

def handle_query_input(query, mode, online):
    """Process a query, possibly changing mode or exiting the loop."""
    query_lower = query.lower()

    if query_lower.startswith("/"):
        command_result = handle_slash_command(query, mode, online)
        return command_result

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
    """Initialize the assistant and run the interaction loop."""
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

    # Authenticate before enabling any capabilities
    if not authenticate_user():
        return  # Exit if authentication fails

    # Determine if online services can be used
    online = is_connected()
    
    # Initialize background daemon for autonomous reminders/tasks
    daemon_callback_message = lambda data: speak(f"Reminder: {data.get('message', 'No message')}") if 'message' in data else None
    daemon_callback_task = lambda data: speak(f"Task due: {data.get('name', 'Task')}")
    initialize_daemon(speak_callback=daemon_callback_message, notify_callback=daemon_callback_task)

    # Start schedule runner for legacy schedule-based tasks
    start_schedule_runner()
    
    # Initialize interrupt handler silently
    try:
        from modules.interrupt_handler import init_interrupt_handler, cleanup_interrupt_handler
        init_interrupt_handler()
    except ImportError:
        cleanup_interrupt_handler = None
    
    greeting = get_greeting(online)

    # --- Modern separator and greeting ---
    separator = Text("-" * 80, style="dim")
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

    # Let the user choose the startup mode (arrow keys)
    mode = select_start_mode(online)
    if mode is None:
        # User cancelled mode selection
        farewell = get_farewell_message()
        console.print(f"[bold magenta]{farewell}[/bold magenta]")
        speak(farewell)
        return

    try:
        while True:
            try:
                query = listen() if mode == 'voice' else prompt_user_input()
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
        # Cleanup daemon and interrupt handler
        stop_schedule_runner()
        shutdown_daemon()
        if cleanup_interrupt_handler:
            cleanup_interrupt_handler()

if __name__ == "__main__":
    main()
