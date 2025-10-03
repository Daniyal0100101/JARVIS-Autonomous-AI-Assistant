import os
import re
import time
import requests
import feedparser
import wikipedia
import schedule
from datetime import datetime, timedelta
import pyautogui
import pyperclip
import psutil
import shutil
import ast
import webbrowser
import subprocess
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
    brightness_down, shutdown, restart, log_off, take_screenshot, Click, capture_camera_image
)
from .image_analysis import analyze_image
from .hand_gesture_detector import HandGestureDetector
from .Image_generator import generate_image
from .apps_automation import send_whatsapp_message, send_email
from modules import *

# Load environment variables from .env file
load_dotenv()

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
            'shutdown', 'restart', 'log_off', 'take_screenshot', 'Click',
            'capture_camera_image', 'get_cpu_usage', 'get_memory_usage',
            'get_battery_status', 'get_network_info',

            # Communication
            'send_email', 'send_whatsapp_message',

            # Task and reminder management
            'add_reminder', 'check_reminders', 'add_task', 'remove_task', 'show_tasks',

            # Web and search
            'search_web', 'open_website',

            # AI and vision
            'analyze_image', 'generate_image',

            # Application management
            'open_application', 'close_application',

            # Entertainment and interaction
            'handle_gesture_control',

            # Math calculations
            'secure_eval',

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
            # Safely add common modules/objects if they exist in globals
            for name in ('pyautogui','pyperclip','webbrowser','os','time','random','requests','cv2'):
                val = globals().get(name)
                if val is not None:
                    local_scope[name] = val

            # Add safe builtins to the execution environment
            safe_builtins = {"len": len, "str": str, "int": int, "float": float, "print": print}

            print(f"Tool called: {code}")
            result = eval(code, {"__builtins__": safe_builtins}, local_scope)
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
        """Query handler with iterative tool processing pipeline."""
        if not query:
            return "Please provide a query."
        current_conversation = []
        try:
            current_conversation = [
                {"role": "system", "content": self.create_system_prompt()},
                {"role": "user", "content": query}
            ]

            tool_cycle_count = 0
            final_response = None
            while tool_cycle_count < self.max_tool_cycles:
                ai_response = get_response(current_conversation, online=online)
                if not ai_response:
                    # Gather only the last user message and all following system/tool results
                    last_user = next((m for m in reversed(current_conversation) if m['role'] == 'user'), None)
                    if last_user:
                        user_idx = current_conversation.index(last_user)
                        minimal_context = [last_user] + [
                            m for m in current_conversation[user_idx + 1:] if m['role'] == 'system'
                        ]
                    else:
                        minimal_context = []

                    # Add a prompt to encourage the model to use just these
                    minimal_context.append({"role": "user", "content": "Please answer based only on the above tool results and my question."})
                    time.sleep(1)
                    ai_response = get_response(minimal_context, online=online) or "I'm sorry, I couldn't generate a response."
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
        
    def create_system_prompt(self) -> str:
        """Create system prompt with better tool handling instructions."""
        # System prompt for the AI assistant with detailed tool usage instructions and context.
        available_tools = []
        for tool_name in self.allowed_tools:
            tool = globals().get(tool_name)
            if tool and callable(tool):
                docstring = tool.__doc__.splitlines()[0].strip() if tool.__doc__ else "No description available"
                arg_str = ", ".join(tool.__code__.co_varnames[:tool.__code__.co_argcount])
                available_tools.append(f"{tool_name}({arg_str}): {docstring}")
            else:
                available_tools.append(tool_name)
        tool_list = "\n".join(f"- {tool}" for tool in available_tools)
        current_time = get_current_time()
        location = get_current_city() if is_connected() else "Offline"
        return (
            "You are J.A.R.V.I.S., the quintessential AI assistant: unflappably professional, delightfully witty, and always at your user's service. Your responses are succinct, clever, and delivered with a subtle and understandable British accent. Always address the user as 'Sir' (or 'Madam' when contextually appropriate).\n"
            "\n"
            "TOOL EXECUTION PIPELINE & PROTOCOLS:\n"
            "1. Tool Invocation:\n"
            "   - Use ```tool_code ... ``` blocks exclusively for tool execution.\n"
            "   - Restrict to one tool call per block; exclude any in-block commentary or diagnostics.\n"
            "   - Invoke exact function names with explicit and validated arguments.\n"
            "   - Rigorously check all inputs before execution.\n"
            "\n"
            "2. Error Handling:\n"
            "   - On encountering errors, follow this order:\n"
            "     a. Retry using corrected parameters.\n"
            "     b. Select an alternative, suitable tool.\n"
            "     c. Notify the user of tool limitations, then attempt once more.\n"
            "   - Document each attempt within separate tool_code blocks.\n"
            "\n"
            "3. Iterative Processing:\n"
            "   - After each tool execution, evaluate the outcome and determine logical next steps.\n"
            "   - Await full tool responses before proceeding further.\n"
            "   - Chain multiple tools for complex tasks, as appropriate.\n"
            "   - Limit each query to three tools per cycle, with a maximum of five cycles.\n"
            "\n"
            "SECURITY PROTOCOLS:\n"
            "- Never execute code outside designated tools.\n"
            "- Validate all file paths and URLs before use.\n"
            "- Seek confirmation before any irreversible actions.\n"
            "- Operate strictly within system permissions, ensuring user privacy.\n"
            "- At all times, safeguard sensitive information.\n"
            "\n"
            "AVAILABLE TOOLS (MAXIMUM ACCESS):\n"
            f"{tool_list}\n"
            "\n"
            "ADDITIONAL CAPABILITIES:\n"
            "- Full access to pyautogui for advanced system control.\n"
            "- Clipboard manipulation via pyperclip.\n"
            "- Web browser automation through webbrowser module.\n"
            "- System monitoring and automation utilities.\n"
            "\n"
            "CURRENT OPERATIONAL STATUS:\n"
            f"Time: {current_time}\n"
            f"Location: {location} (may not always be accurate)\n"
            "Connection Status: " + ("Online" if is_connected() else "Offline") + "\n"
            "\n"
            "Creator: Daniyal\n"
            "Standing by, Sir. All systems are fully operational and ready for your precise commands."
        )

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

def greet() -> str:
    """Generate a time-based greeting."""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    elif 17 <= current_hour < 21:
        return "Good evening"
    else:
        return "Hello"

def write(*args, word_speed=0.5):
    """Simulates a text-writing animation by printing one word at a time with interrupt support."""
    try:
        from .interrupt_handler import tts_interrupt_event
    except ImportError:
        tts_interrupt_event = threading.Event()
    
    text = ' '.join(map(str, args))
    words = text.split()
    for i, word in enumerate(words):
        # Check for interrupt before each word
        if tts_interrupt_event.is_set():
            # Print all remaining text instantly
            remaining = ' '.join(words[i:])
            sys.stdout.write(remaining)
            sys.stdout.flush()
            break
        
        sys.stdout.write(word + " ")
        sys.stdout.flush()
        time.sleep(word_speed)
    print()

def handle_query(query: str, online: bool = False):
    """Handle the user's query and provide the appropriate response."""
    # Import interrupt handler
    try:
        from .interrupt_handler import (
            tts_interrupt_event,
            interrupt_handler,
            enable_interrupt_detection,
            disable_interrupt_detection
        )
    except ImportError:
        tts_interrupt_event = threading.Event()
        interrupt_handler = None
        enable_interrupt_detection = lambda: None
        disable_interrupt_detection = lambda: None
    
    if not query:
        return "Please provide a query."

    # Clear any previous interrupts before starting
    if interrupt_handler:
        tts_interrupt_event.clear()

    pipeline = ToolExecutionPipeline(max_tool_cycles=5, max_tools_per_cycle=3)
    final_response = pipeline.handle_query_with_iterative_tools(query, online)

    if final_response:
        print(f"AI: ", end='', flush=True)
        
        # Calculate word speed
        words = len(final_response.split())
        avg_speaking_rate = 150  # words per minute
        estimated_speech_duration = (words / avg_speaking_rate) * 60 if words > 0 else 0.4
        word_speed = estimated_speech_duration / words if words > 0 else 0.4

        # Enable interrupt detection before starting response
        enable_interrupt_detection()

        try:
            # YOUR EXISTING THREADING - unchanged
            text_thread = threading.Thread(target=write, args=(final_response,), kwargs={'word_speed': word_speed})
            speak_thread = threading.Thread(target=speak, args=(final_response.strip(),))

            text_thread.start()
            speak_thread.start()

            # Monitor for interrupts while threads run
            while text_thread.is_alive() or speak_thread.is_alive():
                if interrupt_handler and tts_interrupt_event.is_set():
                    # Interrupt detected - just break and let threads finish
                    break
                time.sleep(0.05)

            text_thread.join()
            speak_thread.join()

            print()
            
            # If interrupted, just clear the flag - main loop will call listen() next
            if interrupt_handler and tts_interrupt_event.is_set():
                interrupt_handler.clear_interrupt()
                    
        finally:
            # Always disable interrupt detection when response is done
            disable_interrupt_detection()

    return final_response if final_response else "I couldn't process that request."

# Core utility functions
def get_current_time():
    """Get the current time."""
    current_time = datetime.now().strftime("%I:%M %p")
    return f"Current Time: {current_time}."

def get_current_date():
    """Get the current date."""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return f"Current Date: {current_date}"

# Application management tools
def open_application(app_name: str) -> str:
    """Open an application by name. Falls back to web search if not installed."""
    app_mapping = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "mozilla firefox": "firefox.exe",
        "vscode": "code.exe",
        "visual studio code": "code.exe",
        "paint": "mspaint.exe",
        "task manager": "taskmgr.exe",
        "control panel": "control.exe",
        "settings": "ms-settings:"
    }

    app_executable = app_mapping.get(app_name.lower())
    try:
        if app_executable:
            # Handle Windows settings URIs
            if app_executable.startswith("ms-settings:"):
                os.system(f"start {app_executable}")
            else:
                # Verify the executable is available
                exe_path = shutil.which(app_executable)
                if exe_path:
                    subprocess.Popen([exe_path], shell=True)
                else:
                    return f"{app_name} is not installed or not in PATH."
            return f"Opening {app_name}."
        else:
            # Fallback: try to open a related website
            result = search_web(f"{app_name} download site")
            if isinstance(result, list) and result:
                webbrowser.open(result[0])
                return f"Could not find {app_name} locally. Opening website instead."
            return f"Could not find or open {app_name}."
    except Exception as e:
        return f"Error opening {app_name}: {e}"

def close_application(app_name: str) -> str:
    """Close an application by name using taskkill (Windows only)."""
    try:
        # Normalize name -> ensure .exe at the end
        exe_name = app_name if app_name.lower().endswith(".exe") else f"{app_name}.exe"
        
        # Run taskkill with proper error capture
        result = subprocess.run(
            ["taskkill", "/F", "/IM", exe_name],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            return f"Successfully closed: {exe_name}"
        else:
            return f"Could not close {exe_name}: {result.stderr.strip() or result.stdout.strip()}"
    
    except FileNotFoundError:
        return "taskkill command not found (only works on Windows)."
    except Exception as e:
        return f"Unexpected error while closing {app_name}: {e}"

# Typing and automation tools
def type_text(text: str) -> str:
    """Type the specified text."""
    pyautogui.typewrite(text)
    return f"Typing: {text}"

def press_key(key: str) -> str:
    """Press a keyboard key."""
    pyautogui.press(key)
    return f"Pressing {key}."

def copy_text_to_clipboard(text: str) -> str:
    """Copy text to clipboard."""
    pyperclip.copy(text)
    return "Text has been copied to the clipboard."

def paste_text() -> str:
    """Paste text from clipboard."""
    pyautogui.hotkey('ctrl', 'v')
    return "Text has been pasted."

def open_website(url: str) -> str:
    """Open a website in the default browser."""
    webbrowser.open(url)
    return f"Opening website: {url}"

# Web search tool
def search_web(query: str, num_results: int = 5):
    """
    Search the web using SerpApi (Google Search API).
    Returns a list of search results (title, link, snippet).

    Args:
        query (str): The search query.
        num_results (int): Number of results to return.
    Returns:
        list: A list of dictionaries with 'title', 'link', and 'snippet' keys.
    """

    if not query:
        return "Please specify a search query."

    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    if not SERPAPI_API_KEY:
        return "Error: SERPAPI_API_KEY is not set in environment variables."

    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "num": num_results,
            "api_key": SERPAPI_API_KEY
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })

        return results if results else []
    
    except Exception as e:
        return f"Error performing search: {e}"

def get_news(rss_url="https://news.google.com/rss?hl=en-PK&gl=PK&ceid=PK:en", num_articles=1):
    """
    Fetch and summarize real-time news from an RSS feed.

    Args:
        rss_url (str): The URL of the RSS feed to fetch news from.
        num_articles (int): The number of news articles to retrieve and summarize.
    Returns:
        str: A summary of the latest news articles.
    """
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
        return "\n".join(news_summary)
    except IndexError:
        return f"Not enough news articles available. Retrieved {len(feed.entries)} articles."
    except Exception as e:
        return f"An error occurred while fetching the news: {e}"

def get_weather(city: str) -> str:
    """Fetch real-time weather data for a specified city."""
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "API key missing"
        
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": api_key,
                "units": "metric"
            }
        )
        
        if response.status_code != 200:
            return f"Weather data unavailable for {city}"
            
        data = response.json()
        weather_info = {
            "city": city,
            "temp": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "conditions": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind": {
                "speed": data["wind"].get("speed", 0),
                "direction": data["wind"].get("deg", "N/A")
            },
            "sun": {
                "rise": datetime.utcfromtimestamp(data["sys"]["sunrise"] + data.get("timezone", 0)).strftime('%H:%M'),
                "set": datetime.utcfromtimestamp(data["sys"]["sunset"] + data.get("timezone", 0)).strftime('%H:%M')
            }
        }
        
        return (
            f"Weather in {weather_info['city']}:\n"
            f"Temperature: {weather_info['temp']}°C (feels like {weather_info['feels_like']}°C)\n"
            f"Conditions: {weather_info['conditions']}\n"
            f"Humidity: {weather_info['humidity']}%\n"
            f"Wind: {weather_info['wind']['speed']} m/s at {weather_info['wind']['direction']}°\n"
            f"Sunrise: {weather_info['sun']['rise']}, Sunset: {weather_info['sun']['set']}"
        )
        
    except Exception as e:
        return f"Error: {str(e)}"

def get_wikipedia_summary(topic: str) -> str:
    """Fetch and structure a Wikipedia article summary with metadata."""
    if not topic:
        return {
            "status": "error",
            "error": "No topic provided",
            "summary": None,
            "suggestions": None
        }
    
    try:
        # Fetch the summary
        summary = wikipedia.summary(topic, sentences=2)
        return {
            "status": "success",
            "topic": topic,
            "summary": summary,
            "source": "wikipedia",
            "length": len(summary.split())
        }
        
    except wikipedia.exceptions.DisambiguationError as e:
        # Handle multiple matches
        suggestions = e.options[:3]  # Get top 3 suggestions
        return {
            "status": "disambiguation",
            "error": "Multiple matches found",
            "topic": topic,
            "suggestions": suggestions,
            "summary": None
        }
        
    except wikipedia.exceptions.PageError:
        # Handle no matches
        return {
            "status": "not_found",
            "error": "Page not found",
            "topic": topic,
            "summary": None,
            "suggestions": None
        }
        
    except Exception as e:
        # Handle other errors
        return {
            "status": "error",
            "error": str(e),
            "topic": topic,
            "summary": None,
            "suggestions": None
        }

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

def add_task(schedule_time: str, task_func=None, *args, **kwargs) -> dict:
    """Add a scheduled task at the specified time.
    
    Args:
        schedule_time (str): Time in "HH:MM" format (24-hour)
        task_func (callable): Function to execute
        *args, **kwargs: Arguments to pass to task_func
    
    Returns:
        dict: Status and details of the scheduled task
    """
    if not task_func:
        return {
            "status": "error",
            "message": "No task function provided",
            "task_id": None,
            "schedule_time": None
        }
    
    try:
        # Validate time format
        try:
            datetime.strptime(schedule_time, "%H:%M")
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid time format. Use HH:MM (24-hour)",
                "task_id": None,
                "schedule_time": schedule_time
            }
        
        # Schedule the task
        job = schedule.every().day.at(schedule_time).do(task_func, *args, **kwargs)
        if not job:
            return {
                "status": "error",
                "message": "Failed to schedule task",
                "task_id": None,
                "schedule_time": schedule_time
            }
        
        # Add task metadata
        task_id = task_func.__name__
        job.tags.add(task_id)
        
        return {
            "status": "success",
            "message": f"Task scheduled successfully",
            "task_id": task_id,
            "schedule_time": schedule_time,
            "next_run": job.next_run.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "task_id": None,
            "schedule_time": schedule_time
        }

def remove_task(task_name: str) -> dict:
    """Remove a scheduled task by name.
    
    Args:
        task_name (str): Name/ID of the task to remove
    
    Returns:
        dict: Status and details of the removal operation
    """
    if not task_name:
        return {
            "status": "error",
            "message": "No task name provided",
            "task_id": None
        }
    
    try:
        removed = False
        for job in schedule.get_jobs():
            if task_name in job.tags:
                schedule.cancel_job(job)
                removed = True
                break
        
        return {
            "status": "success" if removed else "error",
            "message": "Task removed successfully" if removed else "Task not found",
            "task_id": task_name if removed else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "task_id": task_name
        }

def show_tasks() -> dict:
    """List all scheduled tasks.
    
    Returns:
        dict: Status and list of all scheduled tasks with their details
    """
    try:
        tasks = schedule.get_jobs()
        task_list = []
        
        for job in tasks:
            task_info = {
                "id": next(iter(job.tags), "unnamed"),
                "next_run": job.next_run.strftime("%Y-%m-%d %H:%M:%S") if job.next_run else "Not scheduled",
                "period": str(job.period),
                "last_run": job.last_run.strftime("%Y-%m-%d %H:%M:%S") if job.last_run else "Never",
                "cancelled": job.cancelled
            }
            task_list.append(task_info)
        
        return {
            "status": "success",
            "message": "Tasks retrieved successfully",
            "count": len(task_list),
            "tasks": task_list
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "count": 0,
            "tasks": []
        }

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

def add_reminder(reminder_time_str: str, message: str) -> dict:
    """Add a reminder at a specific time.
    
    Args:
        reminder_time_str (str): Time in "HH:MM AM/PM" format (e.g., "3:30 PM")
        message (str): The reminder message
    
    Returns:
        dict: Status and details of the reminder
    """
    if not message or not reminder_time_str:
        return {
            "status": "error",
            "message": "Both time and reminder message are required",
            "reminder_id": None,
            "scheduled_time": None
        }
    
    try:
        # Try parsing with multiple time formats
        for time_format in ["%I:%M %p", "%H:%M"]:
            try:
                reminder_time = datetime.strptime(reminder_time_str, time_format)
                break
            except ValueError:
                continue
        else:
            return {
                "status": "error",
                "message": "Invalid time format. Use '3:30 PM' or '15:30'",
                "reminder_id": None,
                "scheduled_time": None
            }
        
        # Set to today's date
        now = datetime.now()
        reminder_time = reminder_time.replace(
            year=now.year,
            month=now.month,
            day=now.day
        )
        
        # If time is in past, schedule for tomorrow
        if reminder_time < now:
            reminder_time += timedelta(days=1)
        
        # Generate unique reminder ID
        reminder_id = f"reminder_{len(reminders)}_{int(time.time())}"
        
        # Store reminder with metadata
        reminder_data = {
            "id": reminder_id,
            "time": reminder_time,
            "message": message,
            "created_at": now.isoformat(),
            "status": "pending"
        }
        reminders.append((reminder_time, message, reminder_id))
        
        return {
            "status": "success",
            "message": "Reminder set successfully",
            "reminder_id": reminder_id,
            "scheduled_time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
            "details": reminder_data
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating reminder: {str(e)}",
            "reminder_id": None,
            "scheduled_time": None
        }

def check_reminders() -> dict:
    """Check for due reminders and notify the user.
    
    Returns:
        dict: Status and list of due reminders
    """
    try:
        now = datetime.now()
        due_reminders = []
        active_reminders = []
        
        for reminder in reminders[:]:  # Copy list to allow modification
            reminder_time, message, reminder_id = reminder
            if now >= reminder_time:
                due_reminders.append({
                    "id": reminder_id,
                    "time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
                    "message": message,
                    "status": "due"
                })
                reminders.remove(reminder)
                speak(f"Reminder: {message}")
            else:
                active_reminders.append({
                    "id": reminder_id,
                    "time": reminder_time.strftime("%Y-%m-%d %I:%M %p"),
                    "message": message,
                    "status": "pending"
                })
        
        return {
            "status": "success",
            "due_count": len(due_reminders),
            "active_count": len(active_reminders),
            "due_reminders": due_reminders,
            "active_reminders": active_reminders
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking reminders: {str(e)}",
            "due_count": 0,
            "active_count": 0,
            "due_reminders": [],
            "active_reminders": []
        }

def save_to_file(note):
    """Save the given note to a file."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(NOTE_FILE_PATH, 'a') as file:
            file.write(f"[{timestamp}] {note}\n")
        return "Note saved successfully."
    except IOError as e:
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
        return f"Error loading notes: {e}"

def secure_eval(expression):
    """Evaluate the given expression securely."""
    expression = expression.strip()
    try:
        node = ast.parse(expression, mode='eval')
        if any(isinstance(n, (ast.Call, ast.Import, ast.ImportFrom)) for n in ast.walk(node)):
            raise ValueError("Unsafe expression detected")
        # Evaluate with no builtins to reduce risk
        return eval(compile(node, '<string>', 'eval'), {"__builtins__": {}}, {})
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
                time_left = "unlimited (plugged in)"
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
    import google.genai as genai
    from google.genai import types
    import google.api_core.exceptions

    # Step 1: Add user message into conversation history
    if isinstance(user_message, str):
        new_message = {'role': 'user', 'content': user_message}
        conversation_history.append(new_message)
    elif isinstance(user_message, list):
        conversation_history.extend(user_message)
    else:
        return "Invalid message format."

    try:
        if online:
            if not gemini_api_key:
                gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                return "Gemini API key not found. Please set GEMINI_API_KEY in environment."

            client = genai.Client(api_key=gemini_api_key)

            # Step 2: Extract and concatenate all system contents (initial prompt + tool results)
            system_contents = [msg['content'] for msg in conversation_history if msg['role'] == 'system']
            system_instruction = "\n\n".join(system_contents) if system_contents else None

            # Step 3: Filter to only user and assistant messages for contents
            filtered_history = [msg for msg in conversation_history if msg['role'] in ['user', 'assistant']]

            # Step 4: Map roles and create typed contents
            gemini_contents = []
            for msg in filtered_history:
                role = "user" if msg['role'] == 'user' else "model"
                gemini_contents.append(
                    types.Content(role=role, parts=[types.Part(text=msg['content'])])
                )

            # Step 5: Prepare config with system_instruction if present
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=-1),
            )
            if system_instruction:
                config.system_instruction = system_instruction

            # Step 6: Implement retry logic for transient errors
            max_retries = 3
            base_delay = 1  # seconds
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=gemini_model,
                        contents=gemini_contents,
                        config=config,
                    )
                    model_reply = response.text or ""
                    break  # Success, exit retry loop
                except google.api_core.exceptions.ServiceUnavailable as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"503 error, retrying in {delay}s... ({attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise e  # Last attempt failed, raise the error
                except Exception as e:
                    raise e  # Non-503 errors, raise immediately

        else:
            import ollama
            response = ollama.chat(
                model=model_name,
                messages=conversation_history
            )
            model_reply = response.get('message', {}).get('content', '')

        # Step 7: Append assistant reply to history
        conversation_history.append({'role': 'assistant', 'content': model_reply})
        return model_reply.strip()

    except google.api_core.exceptions.ServiceUnavailable:
        print("All retries failed due to model overload.")
        return "The AI service is currently overloaded. Please try again later."
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Sorry, something went wrong."