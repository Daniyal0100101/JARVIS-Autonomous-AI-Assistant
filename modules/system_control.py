import socket
import pyautogui
import os

def is_connected():
    """Check if the system is connected to the internet."""
    try:
        # Attempt to connect to a known website (Google)
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def lock_screen():
    """Lock the computer screen."""
    try:
        pyautogui.hotkey('win', 'l')
        return "Computer screen locked successfully."
    except Exception as e:
        return f"Failed to lock screen: {e}"

def volume_up():
    """Increase the system volume."""
    try:
        pyautogui.press('volumeup')
        return "Volume increased successfully."
    except Exception as e:
        return f"Failed to increase volume: {e}"

def volume_down():
    """Decrease the system volume."""
    try:
        pyautogui.press('volumedown')
        return "Volume decreased successfully."
    except Exception as e:
        return f"Failed to decrease volume: {e}"

def mute_volume():
    """Mute the system volume."""
    try:
        pyautogui.press('volumemute')
        return "Volume muted successfully."
    except Exception as e:
        return f"Failed to mute volume: {e}"

def unmute_volume():
    """Unmute the system volume."""
    try:
        pyautogui.press('volumemute')
        return "Volume unmuted successfully."
    except Exception as e:
        return f"Failed to unmute volume: {e}"

def play_pause_media():
    """Play or pause the currently playing media."""
    try:
        pyautogui.press('playpause')
        return "Play/pause toggled successfully."
    except Exception as e:
        return f"Failed to toggle play/pause: {e}"

def next_track():
    """Skip to the next media track."""
    try:
        pyautogui.press('nexttrack')
        return "Next track skipped successfully."
    except Exception as e:
        return f"Failed to skip to next track: {e}"

def previous_track():
    """Go back to the previous media track."""
    try:
        pyautogui.press('prevtrack')
        return "Previous track skipped successfully."
    except Exception as e:
        return f"Failed to go to previous track: {e}"

def brightness_up():
    """Increase the screen brightness."""
    try:
        pyautogui.hotkey('fn', 'f12')
        return "Screen brightness increased successfully."
    except Exception as e:
        return f"Failed to increase brightness: {e}"

def brightness_down():
    """Decrease the screen brightness."""
    try:
        pyautogui.hotkey('fn', 'f11')
        return "Screen brightness decreased successfully."
    except Exception as e:
        return f"Failed to decrease brightness: {e}"

def shutdown():
    """Shutdown the computer."""
    try:
        os.system("shutdown /s /t 0")
        return "Shutdown successful."
    except Exception as e:
        return f"Failed to shutdown: {e}"

def restart():
    """Restart the computer."""
    try:
        os.system("shutdown /r /t 0")
        return "Restart successful."
    except Exception as e:
        return f"Failed to restart: {e}"

def log_off():
    """Log off the current user."""
    try:
        os.system("shutdown /l")
        return "Log off successful."
    except Exception as e:
        return f"Failed to log off: {e}"

def take_screenshot():
    """Take a screenshot of the current screen and save it as a PNG file."""
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        return "Screenshot taken successfully."
    except Exception as e:
        return f"Failed to take screenshot: {e}"

def control_system(action):
    """Perform a system control action (e.g., shutdown, restart, etc.) and return a response message."""
    actions = {
        "shutdown": shutdown,
        "restart": restart,
        "log off": log_off,
        "volume up": volume_up,
        "volume down": volume_down,
        "mute": mute_volume,
        "unmute": unmute_volume,
        "play pause": play_pause_media,
        "next track": next_track,
        "previous track": previous_track,
        "brightness up": brightness_up,
        "brightness down": brightness_down,
        "screenshot": take_screenshot
    }

    action_func = actions.get(action.lower())
    
    if action_func:
        return action_func()  # Execute the function and return its response
    else:
        return "Unknown system control action."
