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
    pyautogui.hotkey('win', 'l')
    return "Computer screen locked successfully."

def volume_up():
    """Increase the system volume."""
    pyautogui.press('volumeup')
    return "Volume increased successfully."

def volume_down():
    """Decrease the system volume."""
    pyautogui.press('volumedown')
    return "Volume decreased successfully."

def mute_volume():
    """Mute the system volume."""
    pyautogui.press('volumemute')
    return "Volume muted successfully."

def unmute_volume():
    """Unmute the system volume."""
    pyautogui.press('volumemute')
    return "Volume unmuted successfully."

def play_pause_media():
    """Play or pause the currently playing media."""
    pyautogui.press('playpause')
    return "Play/pause toggled successfully."

def next_track():
    """Skip to the next media track."""
    pyautogui.press('nexttrack')
    return "Next track skipped successfully."

def previous_track():
    """Go back to the previous media track."""
    pyautogui.press('prevtrack')
    return "Previous track skipped successfully."

def brightness_up():
    """Increase the screen brightness."""
    pyautogui.hotkey('fn', 'f12')
    return "Screen brightness increased successfully."

def brightness_down():
    """Decrease the screen brightness."""
    pyautogui.hotkey('fn', 'f11')
    return "Screen brightness decreased successfully."

def shutdown():
    """Shutdown the computer."""
    os.system("shutdown /s /t 0")
    return "Shutdown successful."

def restart():
    """Restart the computer."""
    os.system("shutdown /r /t 0")
    return "Restart successful."

def log_off():
    """Log off the current user."""
    os.system("shutdown /l")
    return "Log off successful."

def take_screenshot():
    """Take a screenshot of the current screen and save it as a PNG file."""
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    return "Screenshot taken successfully."

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
