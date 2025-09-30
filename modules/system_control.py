import socket
import pyautogui
import os
import subprocess
import shlex

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

def take_screenshot(filename: str  = "screenshot.png") -> str:
    """Take a screenshot and save it to the specified filename. Defaults to 'screenshot.png'."""
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        return "Screenshot taken successfully."
    except Exception as e:
        return f"Failed to take screenshot: {e}"

def capture_camera_image(filename: str = "camera_image.png") -> str:
    """Capture an image from the webcam and save it to the specified filename. Defaults to 'camera_image.png'."""

    try:
        import cv2
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return "Failed to access the camera."
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(filename, frame)
            cap.release()
            cv2.destroyAllWindows()
            return "Camera image captured successfully."
        else:
            cap.release()
            cv2.destroyAllWindows()
            return "Failed to capture image from camera."
        
    except ImportError:
        return "OpenCV is not installed. Please install it with 'pip install opencv-python'."
    except Exception as e:
        return f"Failed to capture camera image: {e}"

def Click(x: int, y: int):
    """Simulate a mouse click at the specified (x, y) coordinates."""
    try:
        pyautogui.click(x, y)
        return f"Clicked at ({x}, {y}) successfully."
    except Exception as e:
        return f"Failed to click at ({x}, {y}): {e}"

def system_cli(command: str):
    """A compact CLI interface to execute safe commands only."""
    dangerous_keywords = [
        'shutdown', 'reboot', 'rm', 'del', 'format', 'mkfs', 'dd', 'poweroff',
        'init', 'halt', 'kill', 'taskkill', 'rd', 'rmdir', 'net user', 'net localgroup',
        'reg', 'diskpart', 'chkdsk', 'bootrec', 'bcdedit', 'attrib', 'erase', 'logout',
        'logoff', 'sudo', 'su', 'passwd', 'userdel', 'usermod', 'groupdel', 'chmod', 'chown'
    ]
    tokens = shlex.split(command.lower())
    for keyword in dangerous_keywords:
        if any(keyword in token for token in tokens):
            return f"Command contains dangerous keyword: '{keyword}'. Execution blocked."
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error executing command: {e}"
