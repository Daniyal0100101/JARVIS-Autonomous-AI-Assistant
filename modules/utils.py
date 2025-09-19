import os
import re
import time
import random
import requests
import feedparser
import wikipedia
import schedule
from datetime import datetime, timedelta
import pyautogui
import pyperclip
import psutil
import cv2
import shutil
import smtplib
import ast
import webbrowser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googlesearch import search
from pywinauto import Application
import html
import sys
import threading
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple

# Import custom modules (consolidated)
from .text_to_speech import speak
from .speech_recognition import listen
from .system_control import (
    system_cli, is_connected, lock_screen, volume_up, volume_down, mute_volume, 
    unmute_volume, play_pause_media, next_track, previous_track, brightness_up, 
    brightness_down, shutdown, restart, log_off, take_screenshot
)
from .object_detection import model
from .hand_gesture_detector import HandGestureDetector
from .Image_generator import generate_image
from .apps_automation import send_whatsapp_message
from modules import *

# Load environment variables from .env file
load_dotenv()

# Global variables
conversation_history = []
reminders = []
NOTE_FILE_PATH = "jarvis_notes.txt"

class ToolExecutionPipeline:
    """tool execution pipeline with iterative processing capabilities."""

    def __init__(self, max_tool_cycles=5, max_tools_per_cycle=3):
        self.max_tool_cycles = max_tool_cycles
        self.max_tools_per_cycle = max_tools_per_cycle
        self.conversation_history = []
        self.tool_execution_log = []

        # Comprehensive tool registry - consolidated and deduplicated
        self.allowed_tools = {
            # Core utility functions
            'get_weather', 'get_news', 'get_wikipedia_summary',
            'get_current_city', 'get_current_date', 'get_current_time',

            # File operations
            'copy_file', 'move_file', 'delete_file', 'search_file',
            'save_to_file', 'load_from_file', 'create_directory', 'list_directory',

            # System operations
            'get_system_info', 'system_cli', 'is_connected',
            'lock_screen', 'volume_up', 'volume_down', 'mute_volume',
            'unmute_volume', 'play_pause_media', 'next_track',
            'previous_track', 'brightness_up', 'brightness_down',
            'shutdown', 'restart', 'log_off', 'take_screenshot',
            'get_battery_status', 'get_network_info',

            # Communication
            'send_email', 'send_whatsapp_message',

            # Task and reminder management
            'add_reminder', 'check_reminders', 'add_task', 'remove_task', 'show_tasks',

            # Web and search
            'search_web', 'open_website',

            # AI and detection
            'perform_object_detection', 'generate_image',

            # Application management
            'open_application', 'close_application',

            # Entertainment and interaction
            'handle_gesture_control',

            # Math and calculations
            'secure_eval', 'calculate',

            # Automation
            'type_text', 'press_key', 'copy_text_to_clipboard', 'paste_text',
        }

    def extract_tool_calls(self, text: str) -> List[str]:
        """Extract all tool calls from the text."""
        pattern = r"```tool_code\s*(.*?)\s*```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [match.strip() for match in matches if match.strip()]

    def validate_tool_call(self, code: str) -> Tuple[bool, str]:
        """Validate a tool call for security and syntax."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name not in self.allowed_tools and func_name not in ['len', 'str', 'int', 'float', 'list', 'dict', 'print']:
                            return False, f"Function '{func_name}' is not an allowed tool"
            return True, "Valid"
        except SyntaxError as e:
            return False, f"Invalid code syntax: {str(e)}"

    def execute_tool_call(self, code: str) -> Dict[str, Any]:
        """Execute a single tool call with comprehensive error handling."""
        execution_start = time.time()
        try:
            # Create expanded local scope with maximum access
            local_scope = {tool: globals()[tool] for tool in self.allowed_tools if tool in globals()}
            local_scope.update({
                'pyautogui': pyautogui,
                'pyperclip': pyperclip,
                'webbrowser': webbrowser,
                'os': os,
                'time': time,
                'random': random,
                'requests': requests,
                'cv2': cv2,
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
            })

            print(f"Executing tool call: {code}")
            result = eval(code, {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "print": print}}, local_scope)
            execution_time = time.time() - execution_start
            return {
                'success': True,
                'result': result,
                'code': code,
                'execution_time': execution_time,
                'error': None
            }
        except Exception as e:
            execution_time = time.time() - execution_start
            error_msg = f"Error executing tool '{code}': {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'result': None,
                'code': code,
                'execution_time': execution_time,
                'error': error_msg
            }

    def process_tool_cycle(self, ai_response: str) -> Tuple[List[Dict], bool]:
        """Process a single cycle of tool execution."""
        tool_calls = self.extract_tool_calls(ai_response)
        if not tool_calls:
            return [], False
        tool_calls = tool_calls[:self.max_tools_per_cycle]
        execution_results = []
        has_errors = False
        for tool_call in tool_calls:
            is_valid, validation_msg = self.validate_tool_call(tool_call)
            if not is_valid:
                result = {
                    'success': False,
                    'result': None,
                    'code': tool_call,
                    'execution_time': 0,
                    'error': f"Validation failed: {validation_msg}"
                }
                has_errors = True
            else:
                result = self.execute_tool_call(tool_call)
                if not result['success']:
                    has_errors = True
            execution_results.append(result)
            self.tool_execution_log.append(result)
        return execution_results, has_errors

    def handle_query_with_iterative_tools(self, query: str, online: bool = False) -> str:
        """query handler with iterative tool processing pipeline."""
        if not query:
            return "Please provide a query."
        current_conversation = []
        try:
            current_time = time.strftime('%I:%M %p')
            try:
                location = requests.get('https://ipinfo.io', timeout=5).json()
                user_city = location.get('city', 'Unknown')
                user_country = location.get('country', 'Unknown')
            except:
                user_city = 'Unknown'
                user_country = 'Unknown'
            system_prompt = self.create_system_prompt(current_time, user_city, user_country)
            current_conversation = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            tool_cycle_count = 0
            final_response = None
            while tool_cycle_count < self.max_tool_cycles:
                ai_response = get_response(current_conversation, online=online)
                if not ai_response:
                    final_response = "I apologize, but I couldn't generate a response."
                    break
                tool_results, has_errors = self.process_tool_cycle(ai_response)
                current_conversation.append({"role": "assistant", "content": ai_response})
                if not tool_results:
                    final_response = ai_response
                    break
                for result in tool_results:
                    content = str(result['result']) if result['success'] else str(result['error'])
                    current_conversation.append({"role": "system", "content": content})
                tool_cycle_count += 1
                if tool_cycle_count >= self.max_tool_cycles:
                    final_response = get_response(current_conversation, online=online)
                    if final_response and self.extract_tool_calls(final_response):
                        final_response = "I've completed the available tool operations. " + \
                                         re.sub(r'```tool_code.*?```', '', final_response, flags=re.DOTALL).strip()
                    break
            self.conversation_history.extend(current_conversation)
            return final_response or "I apologize, but I couldn't complete the request."
        except Exception as e:
            error_msg = f"An error occurred while processing your query: {str(e)}"
            print(error_msg)
            return error_msg

    def create_system_prompt(self, current_time: str, user_city: str, user_country: str) -> str:
        """Create system prompt with better tool handling instructions."""
        return f"""You are J.A.R.V.I.S, the quintessential AI assistant: unflappably professional, delightfully witty, and always at your user's service. Your responses are crisp, clever, and delivered with a understandable British accent. Address the user as 'Sir' (or 'Madam' if contextually appropriate).

TOOL EXECUTION PIPELINE:

CRITICAL INSTRUCTIONS:
1. When needing to use tools, output ONLY the tool code blocks without any additional narrative or explanations.
2. Ensure each tool call is placed in its own ```tool_code``` block. Never combine tool calls with any text or context in the same message.
3. Use precise and accurate command formats. For example, when invoking close_application, refer to the exact process name as defined in the mapping (e.g., use "Notepad" for Notepad.exe, "Google Chrome" for chrome, and "Command Prompt" for cmd).
4. Should a tool call return an error, reassess the command syntax and, if necessary, reissue the command or utilize an alternative tool (such as system_cli) with accurate arguments. Do not mix error explanations with tool calls.
5. Always wait for tool execution results before issuing any final response.
6. In your final reply, incorporate tool responses in a clear, concise manner without redundant instructions.

AVAILABLE TOOLS (MAXIMUM ACCESS):
CORE FUNCTIONS:
- get_weather(city) - Weather information
- get_news(num_articles=3) - Latest news
- get_wikipedia_summary(topic) - Wikipedia summaries
- get_current_date() - Current date
- get_current_time() - Current time

FILE OPERATIONS:
- copy_file(src, dst) - Copy files
- move_file(src, dst) - Move files
- delete_file(path) - Delete files
- search_file(directory, search_term) - Search for files
- save_to_file(note) - Save notes
- load_from_file() - Load saved notes
- create_directory(path) - Create directories
- list_directory(path) - List directory contents

SYSTEM CONTROL:
- get_system_info() - System status
- system_cli(command: str) - CLI interface to execute system commands
- is_connected() - Internet connection status
- lock_screen() - Lock computer
- volume_up/down() - Volume control
- mute_volume/unmute_volume() - Mute control
- play_pause_media() - Media control
- next_track/previous_track() - Track control
- brightness_up/down() - Brightness control
- shutdown/restart/log_off() - Power management
- take_screenshot() - Screenshot capture
- get_battery_status() - Battery information
- get_network_info() - Network details

COMMUNICATION:
- send_email(subject, body, to_email) - Email sending
- send_whatsapp_message(recipient_name, message_content) - WhatsApp messaging

TASK MANAGEMENT:
- add_reminder(reminder_time_str, message) - Set reminders
- check_reminders() - Check due reminders
- add_task(schedule_time, task_func, *args) - Schedule tasks
- remove_task(task_name) - Remove tasks
- show_tasks() - Display all tasks

WEB & SEARCH:
- search_web(search_term, num_results=1) - Web search
- open_website(url) - Open websites

AI & DETECTION:
- perform_object_detection() - Camera object detection
- generate_image(prompt) - AI image generation

AUTOMATION:
- open_application(app_name) - Open applications
- close_application(app_name) - Close applications
- type_text(text) - Type text
- press_key(key) - Press keyboard keys
- copy_text_to_clipboard(text) - Copy to clipboard
- paste_text() - Paste from clipboard
- Additional functions for pyautogui, pyperclip, and webbrowser operations

CURRENT STATE:
Current time: {current_time}
User location: {user_city}, {user_country}

At your command, Sir. All systems are operational and primed for precise and unambiguous tool execution. """

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get statistics about tool execution."""
        if not self.tool_execution_log:
            return {"total_executions": 0}
        successful = sum(1 for log in self.tool_execution_log if log['success'])
        failed = len(self.tool_execution_log) - successful
        avg_time = sum(log['execution_time'] for log in self.tool_execution_log) / len(self.tool_execution_log)
        return {
            "total_executions": len(self.tool_execution_log),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(self.tool_execution_log)) * 100,
            "average_execution_time": avg_time
        }

def greet():
    """Generate a greeting based on the current time."""
    hr = int(time.strftime('%H'))
    if 4 < hr < 12:
        return "Good morning"
    elif 12 <= hr < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def write(*args, word_speed=0.5):
    """Simulates a text-writing animation by printing one word at a time."""
    text = ' '.join(map(str, args))
    words = text.split()
    for word in words:
        sys.stdout.write(word + " ")
        sys.stdout.flush()
        time.sleep(word_speed)
    print()

def handle_query(query: str, online: bool = False):
    """Handle the user's query and provide the appropriate response."""
    if not query:
        return "Please provide a query."
    pipeline = ToolExecutionPipeline(max_tool_cycles=5, max_tools_per_cycle=3)
    final_response = pipeline.handle_query_with_iterative_tools(query, online)
    if final_response:
        print(f"AI: ", end='', flush=True)
        words = len(final_response.split())
        avg_speaking_rate = 150  # words per minute
        estimated_speech_duration = (words / avg_speaking_rate) * 60 if words > 0 else 0.4
        word_speed = estimated_speech_duration / words if words > 0 else 0.4
        text_thread = threading.Thread(target=write, args=(final_response,), kwargs={'word_speed': word_speed})
        speak_thread = threading.Thread(target=speak, args=(final_response.strip(),))
        text_thread.start()
        speak_thread.start()
        text_thread.join()
        speak_thread.join()
        print()

# Core utility functions
def get_current_time():
    """Get the current time."""
    current_time = datetime.now().strftime("%I:%M %p")
    return f"{random.choice(['The time now is', 'The current time is', 'It is'])} {current_time}."

def get_current_date():
    """Get the current date."""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return f"Current date: {current_date}"

def calculate(expression):
    """Calculate mathematical expressions safely."""
    WORD_TO_OPERATOR = {
        'plus': '+', 'add': '+', 'sum': '+',
        'minus': '-', 'subtract': '-', 'difference': '-',
        'multiply': '*', 'times': '*', 'product': '*',
        'divide': '/', 'divided by': '/', 'quotient': '/'
    }
    try:
        for word, operator in WORD_TO_OPERATOR.items():
            expression = expression.replace(word, operator)
        expression = ''.join(re.findall(r'[0-9\+\-\*\/\.\(\)\s]+', expression))
        result = secure_eval(expression)
        return f"The result of {expression} is: {result}"
    except Exception as e:
        return f"Error in calculation: {e}"

# Application management tools
def open_application(app_name):
    """Open an application by name."""
    app_mapping = {
        "notepad": "notepad",
        "calculator": "calc",
        "cmd": "cmd",
        "command prompt": "cmd",
        "explorer": "explorer",
        "file explorer": "explorer",
        "chrome": "chrome",
        "google chrome": "chrome",
        "firefox": "firefox",
        "mozilla firefox": "firefox",
        "vscode": "code",
        "visual studio code": "code",
        "paint": "mspaint",
        "task manager": "taskmgr",
        "control panel": "control",
        "settings": "ms-settings:"
    }
    app_executable = app_mapping.get(app_name.lower())
    if app_executable:
        try:
            if app_executable.startswith("ms-settings:"):
                os.system(f"start {app_executable}")
            else:
                os.startfile(app_executable)
            return f"Opening {app_name}."
        except Exception as e:
            return f"Error opening {app_name}: {e}"
    else:
        result = search_web(f"{app_name} website")
        if isinstance(result, list) and result:
            webbrowser.open(result[0])
            return f"Opening {app_name} website."
        else:
            return f"Could not find {app_name}."

def close_application(app_name):
    """Close an application by name."""
    try:
        os.system(f"taskkill /F /IM {app_name}.exe")
        return f"Closing {app_name}."
    except Exception as e:
        try:
            app = Application().connect(active_only=True)
            app.windows()[0].close()
            return "Closing the front-running application."
        except Exception as e2:
            return f"Error closing application: {e2}"

# Typing and automation tools
def type_text(text):
    """Type the specified text."""
    pyautogui.typewrite(text)
    return f"Typing: {text}"

def press_key(key):
    """Press a keyboard key."""
    pyautogui.press(key)
    return f"Pressing {key}."

def copy_text_to_clipboard(text):
    """Copy text to clipboard."""
    pyperclip.copy(text)
    return "Text has been copied to the clipboard."

def paste_text():
    """Paste text from clipboard."""
    pyautogui.hotkey('ctrl', 'v')
    return "Text has been pasted."

def open_website(url):
    """Open a website in the default browser."""
    webbrowser.open(url)
    return f"Opening website: {url}"

# Web search tool
def search_web(search_term, num_results=1):
    """Search the web for the given term."""
    if search_term:
        try:
            results = list(search(search_term, num_results=num_results, lang='en'))
            return results if results else []
        except Exception as e:
            return f"Error performing search: {e}"
    else:
        return "Please specify a search query."

def get_news(rss_url="https://news.google.com/rss?hl=en-PK&gl=PK&ceid=PK:en", num_articles=1):
    """Fetch and summarize real-time news from an RSS feed."""
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            return "No news articles found in the provided RSS feed."
        news_summary = []
        for i in range(min(num_articles, len(feed.entries))):
            entry = feed.entries[i]
            snippet = re.sub('<[^<]+?>', '', entry.description)
            snippet = html.unescape(snippet)
            snippet = snippet[:500] + '...' if len(snippet) > 600 else snippet
            snippet = re.sub(r'http\S+', '', snippet)
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            news_summary.append(f"{i + 1}. {entry.title}\n   {snippet}\n")
        response = "Here's the latest news:\n" + "\n".join(news_summary).strip()
        return response
    except IndexError:
        return f"Not enough news articles available. Retrieved {len(feed.entries)} articles."
    except Exception as e:
        return f"An error occurred while fetching the news: {e}"

def get_weather(city):
    """Fetch real-time weather data for a specified city with detailed forecast."""
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "The API key is missing from the file."
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(base_url)
        data = response.json()
        if data.get("cod") != 200:
            return f"Could not find weather information for {city}. Please check the city name or try again later."
        main = data["main"]
        weather = data["weather"][0]
        wind = data.get("wind", {})
        clouds = data.get("clouds", {})
        sys_info = data.get("sys", {})
        timezone_offset = data.get("timezone", 0)
        temperature = main.get("temp")
        feels_like = main.get("feels_like")
        humidity = main.get("humidity")
        pressure = main.get("pressure")
        weather_description = weather.get("description")
        wind_speed = wind.get("speed", 0)
        wind_deg = wind.get("deg", "N/A")
        visibility = data.get("visibility", "N/A")
        cloudiness = clouds.get("all", "N/A")
        sunrise_time = sys_info.get("sunrise")
        sunset_time = sys_info.get("sunset")
        if sunrise_time and sunset_time:
            sunrise = datetime.utcfromtimestamp(sunrise_time + timezone_offset).strftime('%H:%M:%S')
            sunset = datetime.utcfromtimestamp(sunset_time + timezone_offset).strftime('%H:%M:%S')
        else:
            sunrise = sunset = "N/A"
        message = (
            f"Current weather in {city}:\n"
            f"Temperature: {temperature:.1f}°C (feels like {feels_like:.1f}°C)\n"
            f"Conditions: {weather_description.capitalize()}\n"
            f"Humidity: {humidity}%\n"
            f"Wind: {wind_speed} m/s\n"
            f"Visibility: {visibility} meters\n"
            f"Sunrise: {sunrise}\n"
            f"Sunset: {sunset}\n"
            f"Cloudiness: {cloudiness}%\n"
            f"Pressure: {pressure} hPa\n"
            f"Wind Direction: {wind_deg}°\n"
        )
        return message
    except Exception as e:
        return f"An error occurred while fetching the weather data: {str(e)}"

def get_wikipedia_summary(topic):
    """Fetches a summary from Wikipedia for the given topic."""
    try:
        summary = wikipedia.summary(topic, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:3])
        return f"Multiple results found for '{topic}'. Did you mean one of these: {options}?"
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{topic}'. Please try a different search term."
    except Exception as e:
        return f"An error occurred while fetching the Wikipedia summary: {e}"

def get_system_info():
    """Generate a detailed system report with error handling."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        total_memory = memory.total / (1024 ** 3)
        available_memory = memory.available / (1024 ** 3)
        memory_usage = memory.percent
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_percent = battery.percent
                power_status = "plugged in" if battery.power_plugged else "running on battery"
                battery_status = f"Battery is at {battery_percent}% and {power_status}"
            else:
                battery_status = "No battery detected (desktop system or battery information unavailable)"
        except Exception as e:
            battery_status = f"Unable to get battery information: {str(e)}"
        system_info = (
            f"System Status Report:\n"
            f"Battery: {battery_status}\n"
            f"CPU Usage: {cpu_usage}%\n"
            f"Memory: {memory_usage}% used\n"
            f"RAM: {total_memory:.1f}GB total, {available_memory:.1f}GB available"
        )
        return system_info
    except Exception as e:
        return f"Error gathering system information: {str(e)}"

def get_current_city():
    """Get the current city based on the IP address."""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_address = response.json().get('ip')
        response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=5)
        location = response.json()
        city = location.get('city')
        return city if city else None
    except Exception:
        return None

def add_task(schedule_time, task_func=None, *args, **kwargs):
    """Add a scheduled task at the specified time."""
    try:
        if not task_func:
            return "Error: No task function provided"
        job = schedule.every().day.at(schedule_time).do(task_func, *args, **kwargs)
        if not job:
            return "Error: Could not schedule task"
        job.tags.add(task_func.__name__)
        return f"Task '{task_func.__name__}' scheduled for {schedule_time}."
    except ValueError as e:
        return f"Invalid schedule time format: {e}"
    except Exception as e:
        return f"Error scheduling task: {e}"

def remove_task(task_name):
    """Remove a scheduled task by name."""
    try:
        if not task_name:
            return "Error: No task name provided"
        removed = False
        for job in schedule.get_jobs():
            if task_name in job.tags:
                schedule.cancel_job(job)
                removed = True
        return f"Task '{task_name}' removed successfully." if removed else f"No task found with name '{task_name}'."
    except Exception as e:
        return f"Error removing task: {e}"

def show_tasks():
    """Show all scheduled tasks."""
    try:
        tasks = schedule.get_jobs()
        if not tasks:
            return "No scheduled tasks found."
        task_list = []
        for job in tasks:
            next_run = job.next_run.strftime("%Y-%m-%d %H:%M:%S") if job.next_run else "Not scheduled"
            task_list.append(f"Task: {', '.join(job.tags)} | Next run: {next_run}")
        return "Scheduled tasks:\n" + "\n".join(task_list)
    except Exception as e:
        return f"Error showing tasks: {e}"

def send_email(subject, body, to_email):
    """Send an email with the specified subject, body, and recipient."""
    EMAIL_CREDENTIALS_PATH = os.path.join("Requirements", "email_credentials.txt")
    if not all([subject, body, to_email]):
        return "Error: Subject, body, and recipient email are required."
    if not os.path.exists(EMAIL_CREDENTIALS_PATH):
        return f"Error: Email credentials file not found at {EMAIL_CREDENTIALS_PATH}"
    try:
        with open(EMAIL_CREDENTIALS_PATH, "r") as f:
            credentials = f.read().strip().split('\n')
            if len(credentials) < 2:
                return "Error: Invalid email credentials format"
            from_email = credentials[0].strip()
            password = credentials[1].strip()
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
        return "Email sent successfully."
    except smtplib.SMTPAuthenticationError:
        return "Error: Email authentication failed. Please check your credentials."
    except smtplib.SMTPException as e:
        return f"SMTP error occurred: {str(e)}"
    except TimeoutError:
        return "Error: Connection timed out while sending email."
    except Exception as e:
        return f"Error sending email: {str(e)}"

def copy_file(src, dst):
    """Copy a file to a directory."""
    try:
        shutil.copy(src, dst)
        return f"File copied from {src} to {dst}."
    except Exception as e:
        return f"Error copying file: {e}"

def move_file(src, dst):
    """Move a file to a directory."""
    try:
        shutil.move(src, dst)
        return f"File moved from {src} to {dst}."
    except Exception as e:
        return f"Error moving file: {e}"

def delete_file(path):
    """Delete a file."""
    try:
        os.remove(path)
        return f"File deleted: {path}"
    except Exception as e:
        return f"Error deleting file: {e}"

def search_file(directory, search_term):
    """Search for a file in a directory and its subdirectories."""
    try:
        found_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if search_term.lower() in file.lower():
                    found_files.append(os.path.join(root, file))
        if found_files:
            return f"Found {len(found_files)} file(s):\n" + "\n".join(found_files[:10])
        else:
            return "No matching files found."
    except Exception as e:
        return f"Error searching for file: {e}"

def create_directory(path):
    """Create a new directory."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Directory created: {path}"
    except Exception as e:
        return f"Error creating directory: {e}"

def list_directory(path="."):
    """List contents of a directory."""
    try:
        items = os.listdir(path)
        if items:
            files = [item for item in items if os.path.isfile(os.path.join(path, item))]
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
            result = f"Directory contents for {path}:\n"
            if dirs:
                result += f"Directories ({len(dirs)}): {', '.join(dirs[:10])}\n"
            if files:
                result += f"Files ({len(files)}): {', '.join(files[:10])}"
            return result
        else:
            return f"Directory {path} is empty."
    except Exception as e:
        return f"Error listing directory: {e}"

def add_reminder(reminder_time_str, message):
    """Add a reminder at a specific time."""
    try:
        reminder_time = datetime.strptime(reminder_time_str, "%I:%M %p").replace(
            year=datetime.now().year, month=datetime.now().month, day=datetime.now().day
        )
        if reminder_time < datetime.now():
            reminder_time += timedelta(days=1)
        reminders.append((reminder_time, message))
        return f"Reminder set for {reminder_time.strftime('%I:%M %p')}."
    except ValueError:
        return "Invalid time format. Please provide time in 'HH:MM' format."

def check_reminders():
    """Check if any reminders are due and notify the user."""
    now = datetime.now()
    due_reminders = [reminder for reminder in reminders if now >= reminder[0]]
    for reminder_time, message in due_reminders:
        speak(f"Reminder: {message}")
        reminders.remove((reminder_time, message))
    if due_reminders:
        return f"You have {len(due_reminders)} due reminder(s)."
    else:
        return "No reminders due at this time."

def perform_object_detection():
    """Perform object detection using a pre-trained model."""
    try:
        speak("Activating object detection.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "Failed to open camera."
        detected_objects = []
        while True:
            ret, frame = cap.read()
            if not ret:
                speak("Failed to capture video frame.")
                break
            results = model(frame)
            for *box, conf, cls in results.xyxy[0]:
                cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
                cv2.putText(frame, f"{model.names[int(cls)]} {conf:.2f}", (int(box[0]), int(box[1])-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                detected_objects.append(model.names[int(cls)])
            cv2.imshow('Object Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                speak('Do you have any questions about the objects? If so, say "yes" and ask!')
                reply = listen()
                if reply and "yes" in reply:
                    question = f"Answer the query: {reply.split('yes')[-1].strip()}\nHere are the objects: {', '.join(set(detected_objects))}"
                    message = get_response(question)
                else:
                    message = f"I detected objects: {', '.join(set(detected_objects))}"
                break 
        cap.release()
        cv2.destroyAllWindows()
        return message
    except Exception as e:
        return f"Error in object detection: {e}"

def save_to_file(note):
    """Save the given note to a file."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(NOTE_FILE_PATH, 'a') as file:
            file.write(f"[{timestamp}] {note}\n")
        return "Note saved successfully."
    except IOError as e:
        print(f"Error saving note: {e}")
        return f"Error saving note: {e}"

def load_from_file():
    """Load and return the notes from the file."""
    try:
        if os.path.exists(NOTE_FILE_PATH):
            with open(NOTE_FILE_PATH, 'r') as file:
                notes = file.read()
            return notes if notes else "No notes found."
        else:
            return "No notes found."
    except IOError as e:
        print(f"Error loading notes: {e}")
        return "Error loading notes."

def secure_eval(expression):
    """Evaluate the given expression securely."""
    expression = expression.strip()
    try:
        node = ast.parse(expression, mode='eval')
        if any(isinstance(n, (ast.Call, ast.Import, ast.ImportFrom)) for n in ast.walk(node)):
            raise ValueError("Unsafe expression detected")
        return eval(compile(node, '<string>', 'eval'))
    except Exception as e:
        return f"An error occurred: {e}"

def get_battery_status():
    """Get detailed battery information."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = battery.power_plugged
            status = "charging" if plugged else "discharging"
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours, remainder = divmod(battery.secsleft, 3600)
                minutes, _ = divmod(remainder, 60)
                time_left = f"{int(hours)}h {int(minutes)}m"
            else:
                time_left = "unlimited"
            return f"Battery: {percent}% ({status}), Time remaining: {time_left}"
        else:
            return "No battery detected (desktop system)"
    except Exception as e:
        return f"Error getting battery status: {e}"

def get_network_info():
    """Get network connectivity information."""
    try:
        if is_connected():
            response = requests.get('https://ipinfo.io', timeout=5).json()
            ip = response.get('ip', 'Unknown')
            city = response.get('city', 'Unknown')
            country = response.get('country', 'Unknown')
            isp = response.get('org', 'Unknown')
            return f"Connected to internet. IP: {ip}, Location: {city}, {country}, ISP: {isp}"
        else:
            return "Not connected to the internet."
    except Exception as e:
        return f"Network connected but error getting details: {e}"

def handle_gesture_control():
    """Activate hand gesture control system."""
    try:
        detector = HandGestureDetector()
        detector.start_detection()
        return "Hand gesture control activated. Use your hand to control the cursor."
    except Exception as e:
        return f"Error activating gesture control: {e}"

def add_message(role, content):
    """Add a message to the conversation history."""
    conversation_history.append({'role': role, 'content': content})

def get_response(user_message, model_name='gemma3', online=False,
                 gemini_api_key=None, gemini_model="gemini-2.5-flash"):
    """Get the response from the AI assistant while maintaining conversational history."""
    global conversation_history
    if isinstance(user_message, str):
        new_message = {'role': 'user', 'content': user_message}
    elif isinstance(user_message, list):
        conversation_history.extend(user_message)
        new_message = None
    else:
        return "Invalid message format."
    if new_message:
        conversation_history.append(new_message)
    try:
        if online:
            import google.genai as genai
            from google.genai import types
            import os
            if not gemini_api_key:
                gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                return "Gemini API key not found. Please set GEMINI_API_KEY in your .env file."
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
            client = genai.Client(api_key=gemini_api_key)
            response = client.models.generate_content(
                model=gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                ),
            )
            model_reply = response.text
        else:
            import ollama
            response = ollama.chat(
                model=model_name,
                messages=conversation_history
            )
            model_reply = response.get('message', {}).get('content', '')
        add_message('assistant', model_reply)
        return model_reply.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Sorry, something went wrong."