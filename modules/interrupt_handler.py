"""Keyboard interrupt handler for stopping TTS playback.

Space bar stops current audio playback when enabled and not actively listening
to the microphone. Exposes simple enable/disable flags to coordinate with
speech recognition.
"""

import threading
from pynput import keyboard

# Global interrupt events and state
tts_interrupt_event = threading.Event()
listening_active = threading.Event()
interrupt_enabled = threading.Event()  # Controls when interrupt is allowed


class SimpleInterruptHandler:
    """Minimal keyboard listener that triggers TTS stop on Space."""

    def __init__(self):
        self.running = False
        self.keyboard_listener = None

    def start_listener(self):
        """Start keyboard interrupt listener thread."""
        if self.running:
            return

        self.running = True
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()

    def stop_listener(self):
        """Stop keyboard interrupt listener."""
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def _on_key_press(self, key):
        """Handle key press events and set interrupt flag on Space."""
        try:
            if interrupt_enabled.is_set() and not listening_active.is_set():
                if key == keyboard.Key.space:
                    tts_interrupt_event.set()
        except AttributeError:
            pass

    def clear_interrupt(self):
        """Clear interrupt flag."""
        tts_interrupt_event.clear()

    def is_interrupted(self) -> bool:
        """Return True if an interrupt was triggered."""
        return tts_interrupt_event.is_set()


# Global instance
interrupt_handler = SimpleInterruptHandler()


def init_interrupt_handler():
    """Initialize and start the simple interrupt handler."""
    interrupt_handler.start_listener()


def cleanup_interrupt_handler():
    """Cleanup interrupt handler on exit."""
    interrupt_handler.stop_listener()


def enable_interrupt_detection():
    """Enable interrupt detection (call when starting response)."""
    interrupt_enabled.set()


def disable_interrupt_detection():
    """Disable interrupt detection (call when response finished)."""
    interrupt_enabled.clear()
