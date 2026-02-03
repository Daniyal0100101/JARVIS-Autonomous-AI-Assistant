"""Cross-platform system control helpers.

Provides best-effort actions for lock screen, volume, media controls,
brightness, screenshots, and basic connectivity checks.
"""

import socket
import os
import subprocess
import shlex
import platform
import time

_CONNECTION_CACHE = {"value": None, "ts": 0.0}
_CONNECTION_TTL = 10.0

def is_connected():
    """Return True if a simple TCP connection to a known host succeeds."""
    now = time.monotonic()
    cached = _CONNECTION_CACHE.get("value")
    if cached is not None and (now - _CONNECTION_CACHE.get("ts", 0.0)) < _CONNECTION_TTL:
        return cached
    try:
        # Attempt to connect to a known website (Google)
        conn = socket.create_connection(("www.google.com", 80), timeout=1.5)
        conn.close()
        result = True
    except OSError:
        result = False
    _CONNECTION_CACHE["value"] = result
    _CONNECTION_CACHE["ts"] = now
    return result

def _import_pyautogui():
    try:
        import pyautogui  # type: ignore
        return pyautogui
    except Exception:
        return None


def lock_screen():
    """Lock the computer screen (cross-platform best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                capture_output=True,
                text=True,
                shell=True,
            )
            if result.returncode == 0:
                return "Computer screen locked successfully."
            pg = _import_pyautogui()
            if pg:
                pg.hotkey("win", "l")
                return "Computer screen locked successfully."
            return "Failed to lock screen (pyautogui unavailable)."
        elif system == "Darwin":
            result = subprocess.run(
                ["/usr/bin/osascript", "-e", 'tell application "System Events" to start current screen saver'],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return "Computer screen locked (screensaver started)."
            return f"Failed to start screensaver: {result.stderr.strip()}"
        elif system == "Linux":
            for cmd in (
                ["loginctl", "lock-session"],
                ["gnome-screensaver-command", "-l"],
                ["xdg-screensaver", "lock"],
            ):
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return "Computer screen locked successfully."
            return "Lock screen not supported on this Linux session (no known locker found)."
        else:
            return f"Lock screen not supported on {system}."
    except Exception as e:
        return f"Failed to lock screen: {e}"

def volume_up():
    """Increase the system volume (best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            pg = _import_pyautogui()
            if pg:
                pg.press("volumeup")
                return "Volume increased successfully."
            return "pyautogui not available to control volume."
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'set volume output volume (output volume of (get volume settings) + 6) --100%'], capture_output=True)
            return "Volume up command sent."
        elif system == "Linux":
            for cmd in (
                ["amixer", "-D", "pulse", "sset", "Master", "5%+"],
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
            ):
                if subprocess.run(cmd, capture_output=True).returncode == 0:
                    return "Volume up command sent."
            return "Volume control not supported on this Linux setup."
        else:
            return f"Volume control not supported on {system}."
    except Exception as e:
        return f"Failed to increase volume: {e}"

def volume_down():
    """Decrease the system volume (best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            pg = _import_pyautogui()
            if pg:
                pg.press("volumedown")
                return "Volume decreased successfully."
            return "pyautogui not available to control volume."
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'set volume output volume (output volume of (get volume settings) - 6) --100%'], capture_output=True)
            return "Volume down command sent."
        elif system == "Linux":
            for cmd in (
                ["amixer", "-D", "pulse", "sset", "Master", "5%-"],
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"],
            ):
                if subprocess.run(cmd, capture_output=True).returncode == 0:
                    return "Volume down command sent."
            return "Volume control not supported on this Linux setup."
        else:
            return f"Volume control not supported on {system}."
    except Exception as e:
        return f"Failed to decrease volume: {e}"

def mute_volume():
    """Mute the system volume (best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            pg = _import_pyautogui()
            if pg:
                pg.press("volumemute")
                return "Volume muted successfully."
            return "pyautogui not available to control volume."
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'set volume with output muted'], capture_output=True)
            return "Volume muted."
        elif system == "Linux":
            for cmd in (
                ["amixer", "-D", "pulse", "sset", "Master", "mute"],
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"],
            ):
                if subprocess.run(cmd, capture_output=True).returncode == 0:
                    return "Volume muted."
            return "Mute not supported on this Linux setup."
        else:
            return f"Volume control not supported on {system}."
    except Exception as e:
        return f"Failed to mute volume: {e}"

def unmute_volume():
    """Unmute the system volume (best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            pg = _import_pyautogui()
            if pg:
                pg.press("volumemute")
                return "Volume unmuted successfully."
            return "pyautogui not available to control volume."
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'set volume without output muted'], capture_output=True)
            return "Volume unmuted."
        elif system == "Linux":
            for cmd in (
                ["amixer", "-D", "pulse", "sset", "Master", "unmute"],
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
            ):
                if subprocess.run(cmd, capture_output=True).returncode == 0:
                    return "Volume unmuted."
            return "Unmute not supported on this Linux setup."
        else:
            return f"Volume control not supported on {system}."
    except Exception as e:
        return f"Failed to unmute volume: {e}"

def play_pause_media():
    """Play or pause the currently playing media (best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            pg = _import_pyautogui()
            if pg:
                pg.press("playpause")
                return "Play/pause toggled successfully."
            return "pyautogui not available to control media."
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'tell application "Music" to playpause'], capture_output=True)
            return "Play/pause command sent to Music."
        elif system == "Linux":
            if subprocess.run(["playerctl", "play-pause"], capture_output=True).returncode == 0:
                return "Play/pause toggled."
            return "Media control not supported (playerctl not found)."
        else:
            return f"Media control not supported on {system}."
    except Exception as e:
        return f"Failed to toggle play/pause: {e}"

def next_track():
    """Skip to the next media track (best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            pg = _import_pyautogui()
            if pg:
                pg.press("nexttrack")
                return "Next track skipped successfully."
            return "pyautogui not available to control media."
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'tell application "Music" to next track'], capture_output=True)
            return "Next track command sent to Music."
        elif system == "Linux":
            if subprocess.run(["playerctl", "next"], capture_output=True).returncode == 0:
                return "Next track."
            return "Media control not supported (playerctl not found)."
        else:
            return f"Media control not supported on {system}."
    except Exception as e:
        return f"Failed to skip to next track: {e}"

def previous_track():
    """Go back to the previous media track (best effort)."""
    system = platform.system()
    try:
        if system == "Windows":
            pg = _import_pyautogui()
            if pg:
                pg.press("prevtrack")
                return "Previous track skipped successfully."
            return "pyautogui not available to control media."
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'tell application "Music" to previous track'], capture_output=True)
            return "Previous track command sent to Music."
        elif system == "Linux":
            if subprocess.run(["playerctl", "previous"], capture_output=True).returncode == 0:
                return "Previous track."
            return "Media control not supported (playerctl not found)."
        else:
            return f"Media control not supported on {system}."
    except Exception as e:
        return f"Failed to go to previous track: {e}"

def brightness_up():
    """Increase the screen brightness (best effort, limited support)."""
    system = platform.system()
    try:
        if system == "Windows":
            return "Brightness control not implemented for Windows."
        elif system == "Darwin":
            return "Brightness control not implemented for macOS."
        elif system == "Linux":
            for cmd in (
                ["brightnessctl", "set", "+5%"],
                ["xbacklight", "-inc", "5"],
            ):
                if subprocess.run(cmd, capture_output=True).returncode == 0:
                    return "Brightness increased."
            return "Brightness control not available (requires brightnessctl or xbacklight)."
        else:
            return f"Brightness control not supported on {system}."
    except Exception as e:
        return f"Failed to increase brightness: {e}"

def brightness_down():
    """Decrease the screen brightness (best effort, limited support)."""
    system = platform.system()
    try:
        if system == "Windows":
            return "Brightness control not implemented for Windows."
        elif system == "Darwin":
            return "Brightness control not implemented for macOS."
        elif system == "Linux":
            for cmd in (
                ["brightnessctl", "set", "5%-"],
                ["xbacklight", "-dec", "5"],
            ):
                if subprocess.run(cmd, capture_output=True).returncode == 0:
                    return "Brightness decreased."
            return "Brightness control not available (requires brightnessctl or xbacklight)."
        else:
            return f"Brightness control not supported on {system}."
    except Exception as e:
        return f"Failed to decrease brightness: {e}"

def shutdown():
    """Shutdown the computer (cross-platform)."""
    system = platform.system()
    try:
        if system == "Windows":
            os.system("shutdown /s /t 0")
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'tell application "System Events" to shut down'], capture_output=True)
        elif system == "Linux":
            if subprocess.run(["systemctl", "poweroff"], capture_output=True).returncode != 0:
                os.system("shutdown -h now")
        else:
            return f"Shutdown not supported on {system}."
        return "Shutdown successful."
    except Exception as e:
        return f"Failed to shutdown: {e}"

def restart():
    """Restart the computer (cross-platform)."""
    system = platform.system()
    try:
        if system == "Windows":
            os.system("shutdown /r /t 0")
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'tell application "System Events" to restart'], capture_output=True)
        elif system == "Linux":
            if subprocess.run(["systemctl", "reboot"], capture_output=True).returncode != 0:
                os.system("reboot")
        else:
            return f"Restart not supported on {system}."
        return "Restart successful."
    except Exception as e:
        return f"Failed to restart: {e}"

def log_off():
    """Log off the current user (cross-platform)."""
    system = platform.system()
    try:
        if system == "Windows":
            os.system("shutdown /l")
        elif system == "Darwin":
            subprocess.run(["/usr/bin/osascript", "-e", 'tell application "System Events" to log out'], capture_output=True)
        elif system == "Linux":
            user = os.getenv("USER", "")
            if user:
                if subprocess.run(["loginctl", "terminate-user", user], capture_output=True).returncode != 0:
                    subprocess.run(["gnome-session-quit", "--logout", "--no-prompt"], capture_output=True)
        else:
            return f"Log off not supported on {system}."
        return "Log off successful."
    except Exception as e:
        return f"Failed to log off: {e}"

def take_screenshot(filename: str  = "screenshot.png") -> str:
    """Take a screenshot and save it to the specified filename. Defaults to 'screenshot.png'."""
    try:
        pg = _import_pyautogui()
        if not pg:
            return "pyautogui not available to take screenshots."
        screenshot = pg.screenshot()
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
        pg = _import_pyautogui()
        if not pg:
            return "pyautogui not available to perform clicks."
        pg.click(x, y)
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
