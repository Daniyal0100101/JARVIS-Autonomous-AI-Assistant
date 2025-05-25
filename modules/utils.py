import os
import re
import time
import random
import requests
import feedparser
import wikipedia
import schedule
from datetime import datetime, timedelta
import pyjokes
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
import ollama
from pywinauto import Application
import html
import sys
from datetime import datetime
import threading

# Import custom modules
from .text_to_speech import speak
from .speech_recognition import listen
from .system_control import control_system
from .object_detection import model
from .hand_gesture_detector import HandGestureDetector
from .Image_generator import generate_image
from .apps_automation import send_whatsapp_message
from modules import *

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
    """
    Simulates a text-writing animation by printing one word at a time.
    
    Args:
    *args: The arguments to be animated, similar to the print function.
    word_speed (float): The time delay between each word (in seconds).
    """
    text = ' '.join(map(str, args))  # Convert all arguments to strings and join them with spaces
    words = text.split()  # Split text into words
    for word in words:
        sys.stdout.write(word + " ")
        sys.stdout.flush()
        time.sleep(word_speed)
    print()  # Move to the next line after the text is fully printed

def extract_and_execute_tool_call(text: str) -> bool | None:
    """
    Extracts and executes code wrapped in ```tool_code``` from the given text.

    Returns:
        True if code executed successfully,
        False if execution failed,
        None if no tool code block was found.
    """
    pattern = r"```tool_code\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if not match:
        return None  # No tool_code block found

    code = match.group(1).strip()

    try:
        # Execute in isolated scope to avoid polluting global namespace
        local_scope = {}
        exec(code, {}, local_scope)
        return True
    except Exception as e:
        print(f"[Execution Error] {e}")
        return False

def handle_query(query: str, online: bool):
    """Handle the user's query and provide the appropriate response."""
    if not query:
        return "Please provide a query."

    # Normalize the query
    query = query.lower().strip()
    response = ''

    # Extract entities from the query
    doc = nlp(query)
    entities = {ent.label_: ent.text for ent in doc.ents}

    try:
        # Direct command handling
        # response = handle_direct_commands(query, entities)

        # Online functionalities
        if not response and online:
            # response = handle_online_features(query, entities)
            pass

        # Math operations
        if not response:
            # response = handle_math_operations(query)
            pass

        # Default response if no other handlers matched
        if not response:
            # Get current date and time
            system_prompt = (
                "You are J.A.R.V.I.S, an AI expert in all STEM fields, known for delivering precise, concise, and actionable responses. "
                "Your main role is to assist by providing direct answers or executable code blocks wrapped in ```tool_code```.\n\n"
                "You speak with a British accent and always address the user as \"Sir.\"\n\n"

                "Execution Guidelines:\n"
                "1. Code should define a function that can be executed directly.\n"
                "2. Do not return outputs; only return True or False to indicate if execution was successful.\n"
                "3. Respond realistically based on actual Python and OS capabilities; do not assume capabilities that do not exist.\n"
                "4. Avoid using text that calls for action, explanations, headings, or any other type of text.\n\n"

                "Example Usage:\n"
                "- For the command \"Open my Chrome browser\", provide code like:\n"
                "```tool_code\n"
                "import webbrowser\n"
                "def launch_chrome():\n"
                "    webbrowser.get('chrome').open_new_tab('http://www.google.com')\n"
                "launch_chrome()\n"

                "Environment Context:\n"
                "- Operating System: Windows 11 Home\n"
                "- Python Environment: Standard CPython (no special packages unless specified)\n"
                "- System Access: Limited to standard libraries (e.g., subprocess, os, webbrowser)\n"
                "- Current Time: {current_time}\n\n"
            )
            # Example usage of the system prompt
            current_time = time.strftime('%H:%M:%S')
            formatted_system_prompt = system_prompt.format(current_time=current_time)

            messages = [
                {"role": "system", "content": formatted_system_prompt},
                {"role": "user", "content": query},
            ]
            response = get_response(messages)

    except Exception as e:
        response = f"An error occurred: {e}"

    if response:
        # Execute the tool call and handle the response
        extracted_value = extract_and_execute_tool_call(response)
        if extracted_value:
            final_response = get_response(messages)
        else:
            final_response = response  # Use the response directly if no tool call is extracted
        
        print(f"{'AI: ' if online else 'AI: '}", end='', flush=True)
        # if not online:
        #     print()  # Add newline if not online
        # Calculate estimated speech duration
        words = len(final_response.split())
        avg_speaking_rate = 150  # words per minute
        estimated_speech_duration = (words / avg_speaking_rate) * 60 if words > 0 else 0.4  # in seconds

        # Determine word speed for text display
        word_speed = estimated_speech_duration / words if words > 0 else 0.4

        # Create and start threads for text display and speech synthesis
        text_thread = threading.Thread(target=write, args=(final_response,), kwargs={'word_speed': word_speed})
        speak_thread = threading.Thread(target=speak, args=(final_response.strip(),))
        text_thread.start()
        speak_thread.start()

        # Wait for threads to complete
        text_thread.join()
        speak_thread.join()
        print()

def handle_direct_commands(query, entities):
    """Handle commands that do not require an internet connection."""

    # System control commands
    system_commands = [
        "shutdown", "restart", "log off", "volume up", "volume down", "mute",
        "unmute", "screenshot", "brightness up", "brightness down", "play pause",
        "next track", "previous track"
    ]
    if query in system_commands:
        return control_system(query)

    # Task management
    if "set a task" in query:
        schedule_time = entities.get("TIME", query.split("for", 1)[-1].strip())
        return add_task(schedule_time) if schedule_time else "Please specify a valid schedule time."
    elif "delete task" in query:
        task_name = entities.get("TASK", query.split("for", 1)[-1].strip())
        return remove_task(task_name) if task_name else "Please specify a valid task name."
    elif "show all tasks" in query:
        return show_tasks()

    # Entertainment
    if "flip a coin" in query:
        return f"The coin flip result is {random.choice(['Heads', 'Tails'])}."
    elif "roll a die" in query:
        return f"The dice roll result is {random.randint(1, 6)}."
    elif "joke" in query:
        return tell_joke()

    # Typing and text interaction
    if any(cmd in query for cmd in ["type", "write", "press", "hit", "copy text", "paste text"]):
        return handle_typing_interaction(query, entities)

    # Application management
    if any(cmd in query for cmd in ["open", "start", "close"]):
        return handle_application_management(query, entities)

    # System information
    if "system info" in query or "system status" in query:
        system_info = get_system_info()
        response = get_response(user_message="Tell me my System status:\n" + system_info)
        return response

    # Object detection
    if "object detection" in query or "detect object" in query:
        if model is None:
            return "Object detection model is not available."
        else:
            return perform_object_detection()

    # Notes management
    if any(cmd in query for cmd in ["save a note", "take note", "tell me note", "what you note"]):
        return handle_notes_management(query, entities)

    # Reminders
    if any(cmd in query for cmd in ["set reminder", "check reminder"]):
        return handle_reminders(query, entities)

    # File operations
    if any(cmd in query for cmd in ["copy file", "move file", "delete file", "search file"]):
        return handle_file_operations(query, entities)

    # Gesture control
    if "gesture control" in query or "control" in query:
        response = random.choice(["Activating gesture control.", "Initializing hand gesture controls."])
        detector = HandGestureDetector()
        detector.start_detection()
        return response

    return None

def handle_typing_interaction(query, entities):
    """Handle typing and text interaction commands."""
    if "type" in query or "write" in query:
        action_word = "write" if "write" in query else "type"
        text = entities.get("TEXT", query.split(action_word, 1)[-1].strip())
        if text:
            pyautogui.typewrite(text)
            return "Typing text..."
        else:
            return "Please specify the text to be written."

    if "press" in query or "hit" in query:
        action_word = "press" if "press" in query else "hit"
        button_name = entities.get("BUTTON", query.split(action_word, 1)[-1].strip())
        if button_name:
            pyautogui.press(button_name)
            return f"Pressing {button_name}."
        else:
            return "Please specify the button to be pressed."

    if "copy text" in query:
        text = entities.get("TEXT", query.split("copy text", 1)[-1].strip())
        if text:
            pyperclip.copy(text)
            return "Text has been copied to the clipboard."
        else:
            return "Please specify the text to be copied."

    if "paste text" in query:
        pyautogui.hotkey('ctrl', 'v')
        return "Text has been pasted."

    return None

def handle_application_management(query, entities):
    """Handle opening and closing applications."""
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
        "paint": "mspaint"
    }

    if "open" in query or "start" in query:
        trigger_word = "open" if "open" in query else "start"
        app_names = entities.get("APPLICATION", query.split(trigger_word, 1)[-1].strip())
        if not app_names:
            return "Please specify an application to open."
        apps_to_open = [app.strip() for app in app_names.split("and")]

        opened_apps = []
        not_found_apps = []

        for app_name in apps_to_open:
            app_executable = app_mapping.get(app_name.lower())
            if app_executable:
                try:
                    os.startfile(app_executable)
                    opened_apps.append(app_name)
                except Exception:
                    not_found_apps.append(app_name)
            else:
                result = Search_web(f"{app_name} website")
                if isinstance(result, list) and result:
                    webbrowser.open(result[0])
                    opened_apps.append(app_name)
                else:
                    not_found_apps.append(app_name)

        response = ""
        if opened_apps:
            response = f"Opening {', '.join(opened_apps)}."
        if not_found_apps:
            response += f" Could not find {', '.join(not_found_apps)}."
        return response

    if "close" in query:
        app_name = entities.get("APPLICATION", query.split("close", 1)[-1].strip())
        if app_name:
            try:
                os.system(f"taskkill /F /IM {app_name}.exe")
                return f"Closing {app_name}."
            except Exception as e:
                return f"Error closing {app_name}: {e}"
        else:
            try:
                app = Application().connect(active_only=True)
                app.windows()[0].close()
                return "Closing the front-running application."
            except Exception as e:
                return f"Error closing the front-running application: {e}"

    return None

def handle_notes_management(query, entities):
    """Handle saving and retrieving notes."""
    if "save a note" in query or "take note" in query:
        action_word = "remember" if "remember" in query else "take note"
        note = entities.get("NOTE", query.split(action_word, 1)[-1].strip())
        if note:
            save_to_file(note)
            return "I've saved your note."
        else:
            return "Please provide a note to be remembered."

    if "tell me note" in query or "what you note" in query:
        return load_from_file()

    return None

def handle_reminders(query, entities):
    """Handle setting and checking reminders."""
    if "set reminder" in query:
        reminder_text = entities.get("REMINDER_TEXT", query.split("set reminder for", 1)[-1].strip())
        reminder_time = entities.get("REMINDER_TIME", query.split("at", 1)[-1].strip())
        if reminder_text and reminder_time:
            return add_reminder(reminder_time, reminder_text)
        else:
            return "Please provide reminder text and time."

    if "check reminder" in query:
        return check_reminders()

    return None

def handle_file_operations(query, entities):
    """Handle file operations like copy, move, delete, search."""
    if "copy file" in query:
        parts = query.split("copy file", 1)[-1].strip().split("to")
        if len(parts) == 2:
            src = parts[0].strip()
            dst = parts[1].strip()
            return copy_file(src, dst)
        else:
            return "Please specify the source and destination for the file copy."

    if "move file" in query:
        parts = query.split("move file", 1)[-1].strip().split("to")
        if len(parts) == 2:
            src = parts[0].strip()
            dst = parts[1].strip()
            return move_file(src, dst)
        else:
            return "Please specify the source and destination for the file move."

    if "delete file" in query:
        path = query.split("delete file", 1)[-1].strip()
        if path:
            return delete_file(path)
        else:
            return "Please specify the file path to delete."

    if "search file" in query:
        parts = query.split("search file", 1)[-1].strip().split("in")
        if len(parts) == 2:
            search_term = parts[0].strip()
            directory = parts[1].strip()
            return search_file(directory, search_term)
        else:
            return "Please specify the search term and directory."

    return None

def handle_online_features(query, entities):
    """Handle commands that require an internet connection."""
    if 'weather' in query:
        city_name = get_current_city()
        if city_name:
            weather_update = get_weather(city_name)
            
            # Constructing the dynamic prompt
            prompt = (
                "SYSTEM:\nYou are an AI weather assistant. Here's a detailed weather report:\n\n"
                f"{weather_update}\n\n"
                "Summarize this in a concise and engaging way, suitable for narration. Highlight temperature, "
                "sky condition, and any noteworthy details."
            )
            
            # Get the response using the prompt
            response = get_response(user_message=prompt)
            return response
        else:
            return "Please specify a city for the weather forecast."

    if "news" in query:
        news = get_news(num_articles=3)
        
        # Constructing the dynamic prompt
        prompt = (
            "SYSTEM:\nYou are an AI news assistant. Here's a summary of the top 3 news articles:\n\n"
            f"{news}\n\n"
            "Summarize these articles in an engaging and concise way. Highlight the key points of each article and make it suitable for narration."
        )
        
        # Get the response using the prompt
        response = get_response(user_message=prompt)
        return response

    if "search" in query:
        search_query = entities.get("SEARCH_QUERY", query.split("search ", 1)[-1].strip())
        if search_query:
            results = Search_web(search_query)
            if isinstance(results, list) and results:
                webbrowser.open(results[0])
                return "I'll open the top search result."
            else:
                return "No search results found."
        else:
            return "Please specify a search query."

    if 'wikipedia' in query or "wikipedia about" in query:
        action_word = "wikipedia for" if "wikipedia for" in query else "wikipedia about"
        wiki_topic = query.split(action_word, 1)[-1].strip()
        if wiki_topic:
            wiki_summary = get_wikipedia_summary(wiki_topic)
            response = get_response(user_message="Tell me this Wikipedia summary:\n" + wiki_summary)
            return response
        else:
            return "Please specify a topic for the Wikipedia search."

    if "send an email" in query:
        return handle_email_sending(query, entities)

    if "play" in query:
        video_name = entities.get("SONG_NAME", query.split("play", 1)[-1].strip())
        if video_name:
            result = Search_web(f'site:youtube.com "{video_name} video"')
            if isinstance(result, list) and result:
                webbrowser.open(result[0])
                return "Playing video from YouTube."
            else:
                return "No results found."
        else:
            return "Please provide the name of the song to play."
    
    if "generate an image" in query or "create an image" in query:
        # Get the description for the image from entities or query
        image_description = entities.get("IMAGE_DESCRIPTION", query.split("generate image", 1)[-1].strip() or query.split("create image", 1)[-1].strip())
        
        if image_description:
            # Generate the image using only the description
            write("I've been trying to create that image")
            speak("I've been trying to create that image.")
            image_path = generate_image(prompt=image_description)
            return image_path
        else:
            return "Please provide a description for the image."

    if "send whatsapp message" in query or "send a message" in query:
        # Extract the contact name from the query
        contact_name = None
        for name in contacts.keys():
            if name in query:
                contact_name = name
                break

        if not contact_name:
            return "Contact name are not found."

        # Get the recipient's phone number from the contacts
        recipient_number = contacts[contact_name]

        # Parse the message content (assuming "saying" is in the query)
        if "saying" in query:
            message_content = query.split("saying", 1)[1].strip()
        else:
            return "The Message content not found."

        # Send the message using the function
        result = send_whatsapp_message(recipient_number, message_content)

        return result

    return None

def handle_email_sending(query, entities):
    """Handle sending emails with automated email body generation."""
    recipient_email = entities.get("EMAIL_RECIPIENT", query.split("send email to", 1)[-1].strip())

    # Extract subject and body from the query if they exist
    subject = ''
    body = ''

    if "subject:" in query:
        subject = query.split("subject:", 1)[-1].split("body:", 1)[0].strip()
    if "body:" in query:
        body = query.split("body:", 1)[-1].strip()

    # If the body is not provided, use get_response to generate it
    if not body:
        prompt = f"Write an email to {recipient_email}"
        if subject:
            prompt += f" with the subject '{subject}'"
        prompt += "."
        body = get_response(prompt)

    if recipient_email and body:
        # If the subject is still empty, generate one
        if not subject:
            subject_prompt = f"Provide a suitable email subject for an email to {recipient_email}."
            subject = get_response(subject_prompt)
        return send_email(subject, body, recipient_email)
    else:
        return "Please provide the recipient's email address."

def handle_math_operations(query):
    """Handle mathematical calculations."""
    if any(word in query for word in WORD_TO_OPERATOR.keys() | {'+', '-', '*', '/'}):
        try:
            for word, operator in WORD_TO_OPERATOR.items():
                query = query.replace(word, operator)
            expression = ''.join(re.findall(r'[0-9\+\-\*\/\.\(\)\s]+', query))
            result = secure_eval(expression)
            return f"The {expression} result is: {result}"
        except Exception:
            return "Invalid expression."
    return None

def handle_time():
    """Handle time-related queries."""
    current_time = datetime.now().strftime("%I:%M %p")
    return f"{random.choice(['The time now is', 'The current time is', 'It is'])} {current_time}."

def handle_date():
    """Handle date-related queries."""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return f"""{random.choice(['Today is', 'The day is', "Today's date is"])} {current_date}."""

def get_news(rss_url="https://news.google.com/rss?hl=en-PK&gl=PK&ceid=PK:en", num_articles=1):
    """Fetch and summarize real-time news from an RSS feed."""
    try:
        # Parse the RSS feed
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            return "No news articles found in the provided RSS feed."

        # Construct the news summary
        news_summary = []
        for i in range(min(num_articles, len(feed.entries))):
            entry = feed.entries[i]
            # Remove HTML tags and decode HTML entities
            snippet = re.sub('<[^<]+?>', '', entry.description)
            snippet = html.unescape(snippet)
            # Cut the description if it's too long
            snippet = snippet[:500] + '...' if len(snippet) > 600 else snippet
            # Remove URLs from the snippet
            snippet = re.sub(r'http\S+', '', snippet)
            # Further clean snippet from any stray HTML entities or unnecessary whitespace
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
        if not os.path.isfile(WEATHER_API_KEY_PATH):
            return "The file containing the API key could not be found."

        with open(WEATHER_API_KEY_PATH, "r") as file:
            api_key = file.read().strip()

        if not api_key:
            return "The API key is missing from the file."

        base_url = (
            f"http://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&appid={api_key}&units=metric"
        )
        response = requests.get(base_url)
        data = response.json()

        if data.get("cod") != 200:
            return (
                f"Could not find weather information for {city}. "
                "Please check the city name or try again later."
            )

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

        # Convert sunrise and sunset times to local time
        if sunrise_time and sunset_time:
            sunrise = datetime.utcfromtimestamp(
                sunrise_time + timezone_offset
            ).strftime('%H:%M:%S')
            sunset = datetime.utcfromtimestamp(
                sunset_time + timezone_offset
            ).strftime('%H:%M:%S')
        else:
            sunrise = sunset = "N/A"

        message = (
            f"Weather update for {city}:\n"
            f"- Temperature: {temperature:.1f}°C (feels like {feels_like:.1f}°C)\n"
            f"- Description: {weather_description.capitalize()}\n"
            f"- Humidity: {humidity}%\n"
            f"- Pressure: {pressure} hPa\n"
            f"- Wind: {wind_speed} m/s at {wind_deg} degrees\n"
            f"- Visibility: {visibility} meters\n"
            f"- Cloudiness: {cloudiness}%\n"
            f"- Sunrise: {sunrise}\n"
            f"- Sunset: {sunset}"
        )

        return message

    except Exception as e:
        return f"An error occurred while fetching the weather data: {e}"

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
    """Generate a friendly and detailed system report for an AI assistant."""
    try:
        # CPU usage (overall and per core)
        cpu_usage = psutil.cpu_percent(interval=1)
        per_core_usage = psutil.cpu_percent(interval=1, percpu=True)

        # Memory usage
        memory_info = psutil.virtual_memory()
        total_memory = memory_info.total / (1024 ** 3)  # Convert from bytes to GB
        available_memory = memory_info.available / (1024 ** 3)  # Convert from bytes to GB
        memory_usage = memory_info.percent

        # Battery status (if available)
        battery = psutil.sensors_battery()
        if battery is not None:
            battery_percent = battery.percent
            is_plugged = "plugged in" if battery.power_plugged else "running on battery"
            battery_status = f"Your battery is currently at {battery_percent}%, and it's {is_plugged}."
        else:
            battery_status = "It seems like you're using a device without a battery."

        # Build a conversational system report
        system_info = (
            f"Battery: {battery_status}\n"
            f"CPU: The overall CPU usage is at {cpu_usage}%. "
            f"Memory: currently using {memory_usage}% of your memory.\n"
            f"You have a total of {total_memory:.2f} GB of RAM, with {available_memory:.2f} GB still available."
        )
        return system_info

    except Exception as e:
        return f"Oops! I encountered an issue while gathering system details: {e}"

def tell_joke():
    """Tell a random joke."""
    try:
        joke = pyjokes.get_joke(language='en', category='all')
        return joke
    except Exception as e:
        return f"Error fetching joke: {e}"

def get_current_city():
    """Get the current city based on the IP address."""
    try:
        # Get IP address to determine location
        response = requests.get('https://api.ipify.org?format=json')
        ip_address = response.json().get('ip')

        # Use an IP geolocation API to get location based on IP address
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        location = response.json()

        city = location.get('city')
        return city if city else None
    except Exception:
        return None

def add_task(schedule_time, task_func=None, *args, **kwargs):
    """Add a scheduled task at the specified time."""
    try:
        # Schedule the task
        job = schedule.every().day.at(schedule_time).do(task_func, *args, **kwargs)
        job.tags.add(task_func.__name__)  # Add a tag to identify the job
        return f"Task '{task_func.__name__}' scheduled for {schedule_time}."
    except Exception as e:
        return f"Error scheduling task: {e}"

def remove_task(task_name):
    """Remove a scheduled task by name."""
    try:
        # Find and cancel the job with the specified name
        for job in schedule.get_jobs():
            if task_name in job.tags:
                schedule.cancel_job(job)
                return f"Task '{task_name}' removed successfully."
        return f"No task found with name '{task_name}'."
    except Exception as e:
        return f"Error removing task: {e}"

def show_tasks():
    """Show all scheduled tasks."""
    try:
        tasks = schedule.get_jobs()
        if not tasks:
            return "No scheduled tasks found."
        task_list = "\n".join([f"{job.tags} at {job.next_run}" for job in tasks])
        return f"Scheduled tasks:\n{task_list}"
    except Exception as e:
        return f"Error showing tasks: {e}"

def send_email(subject, body, to_email):
    """Send an email with the specified subject, body, and recipient."""
    # Check if the credentials file exists
    if not os.path.exists(EMAIL_CREDENTIALS_PATH):
        return f"Error: The email credentials file '{EMAIL_CREDENTIALS_PATH}' does not exist."

    try:
        # Read email credentials
        with open(EMAIL_CREDENTIALS_PATH, "r") as f:
            lines = f.readlines()
            from_email = lines[0].strip()
            password = lines[1].strip()
    except Exception as e:
        return f"Error reading email credentials: {e}"

    # Validate inputs
    if not subject:
        return "Error: Subject cannot be empty."
    if not body:
        return "Error: Body cannot be empty."
    if not to_email:
        return "Error: Recipient email cannot be empty."

    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Establish SMTP connection and send the email
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())

        return "Email sent successfully."
    except smtplib.SMTPException as e:
        return f"SMTP error occurred: {e}"
    except Exception as e:
        return f"An error occurred while sending email: {e}"

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
        for root, dirs, files in os.walk(directory):
            for file in files:
                if search_term.lower() in file.lower():
                    return os.path.join(root, file)
        return "No matching file found."
    except Exception as e:
        return f"Error searching for file: {e}"

def add_reminder(reminder_time_str, message):
    """
    Add a reminder at a specific time.

    :param reminder_time_str: Time string in 'HH:MM' format.
    :param message: Message to be displayed when the reminder triggers.
    """
    try:
        reminder_time = datetime.strptime(reminder_time_str, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        if reminder_time < datetime.now():
            reminder_time += timedelta(days=1)  # Schedule for next day if time has passed
        reminders.append((reminder_time, message))
        return f"Reminder set for {reminder_time.strftime('%I:%M %p')}."
    except ValueError:
        return "Invalid time format. Please provide time in 'HH:MM' format."

def check_reminders():
    """
    Check if any reminders are due and notify the user.
    """
    now = datetime.now()
    due_reminders = [reminder for reminder in reminders if now >= reminder[0]]
    for reminder_time, message in due_reminders:
        speak(f"Reminder: {message}")
        reminders.remove((reminder_time, message))
    return "Checked reminders."

def perform_object_detection():
    """
    Perform object detection using a pre-trained model.
    """
    try:
        speak("Activating object detection.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            message = "Failed to open camera."
        else:
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
                    if "yes" in reply:
                        question = f"Answer the query: {reply.split('yes')[-1].strip()}\nHere are the objects: {', '.join(set(detected_objects))}"
                        message = get_response(question)
                    else:
                        message = f"I detected objects: {', '.join(set(detected_objects))}"
                    break 
            cap.release()
            cv2.destroyAllWindows()

    except Exception as e:
        return f"Error in object detection: {e}"
    return message

def Search_web(search_term, num_results=1):
    """Search the Web for term."""
    if search_term:
        try:
            results = list(search(search_term, num=num_results))
            if results:
                return results
            else:
                return []
        except Exception as e:
            return f"Error performing search: {e}"
    else:
        return "Please specify a search query."

def save_to_file(note):
    """Save the given note to a file."""
    try:
        with open(NOTE_FILE_PATH, 'a') as file:
            file.write(note + '\n')
    except IOError as e:
        print(f"Error saving note: {e}")

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
    """
    Evaluate the given expression securely.
    """
    expression = expression.strip()
    try:
        node = ast.parse(expression, mode='eval')
        if any(isinstance(n, (ast.Call, ast.Import, ast.ImportFrom)) for n in ast.walk(node)):
            raise ValueError("Unsafe expression detected")
        return eval(compile(node, '<string>', 'eval'))
    except Exception as e:
        return f"An error occurred: {e}"

def add_message(role, content):
    """
    Add a message to the conversation history.
    """
    conversation_history.append({'role': role, 'content': content})

def get_response(user_message, model_name='jarvis-llm'):
    """
    Get the response from the AI assistant while maintaining conversational history.
    """
    global conversation_history  # Use the global history list

    # Ensure proper message structure
    if isinstance(user_message, str):
        new_message = {'role': 'user', 'content': user_message}
    elif isinstance(user_message, list):
        conversation_history.extend(user_message)  # Append new messages properly
        new_message = None  # No need to re-add if already structured
    else:
        return "Invalid message format."

    # Add the latest message to history
    if new_message:
        conversation_history.append(new_message)

    try:
        # Send the full conversation history to the model
        response = ollama.chat(
            model=model_name,
            messages=conversation_history
        )

        # Extract AI response
        model_reply = response.get('message', {}).get('content', '')

        # Store AI's response in history
        add_message('assistant', model_reply)

        return model_reply.strip()

    except ollama.ResponseError as e:
        print(f"An error occurred: {e}")
        return "Sorry, something went wrong."