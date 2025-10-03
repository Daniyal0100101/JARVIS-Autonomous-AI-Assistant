import threading
from pynput import keyboard

# Global interrupt events and state
tts_interrupt_event = threading.Event()
listening_active = threading.Event()
interrupt_enabled = threading.Event()  # Controls when interrupt is allowed

class SimpleInterruptHandler:
    """Handles interruptions via Space key - just stops response gracefully."""
    
    def __init__(self):
        self.running = False
        self.keyboard_listener = None
        
    def start_listener(self):
        """Start keyboard interrupt listener thread."""
        if self.running:
            return
            
        self.running = True
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()
        
    def stop_listener(self):
        """Stop keyboard interrupt listener."""
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
    def _on_key_press(self, key):
        """Handle key press events."""
        try:
            # Only trigger interrupt if:
            # 1. Interrupt is enabled (response is playing)
            # 2. Main listening is not active
            # 3. The key is Space
            if interrupt_enabled.is_set() and not listening_active.is_set():
                if key == keyboard.Key.space:
                    # Just trigger interrupt to stop response
                    tts_interrupt_event.set()
                    
        except AttributeError:
            pass
            
    def clear_interrupt(self):
        """Clear interrupt flag."""
        tts_interrupt_event.clear()
        
    def is_interrupted(self) -> bool:
        """Check if interrupt was triggered."""
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
