# Jarvis AI Assistant

Jarvis is an advanced, cross-platform AI assistant for Windows and Mac, built with Python. It delivers a seamless voice and text-driven experience in a feature-rich command-line interface, offering intelligent system control, automation, and AI-powered tools—all enhanced by interactive visual feedback.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## 🌟 Key Features

### 🎤 Voice & Speech
- **Faster-Whisper Speech Recognition**: High-accuracy, efficient speech-to-text transcription
- **Dual TTS System**: StreamElements API for online TTS with `pyttsx3` offline fallback
- **Voice/Text Mode Switching**: Seamlessly switch between input modes during conversation
- **Interrupt Detection**: Stop AI responses mid-sentence with new commands

### 🖥️ System Control
- **Power Management**: Shutdown, restart, log off
- **Media Controls**: Play/pause, next/previous track, volume adjustment
- **Display**: Brightness control, screenshot capture
- **Security**: Screen lock, password-protected authentication

### 🤖 AI-Powered Tools
- **Image Generation**: Create images from text prompts using DALL-E 3
- **Image Analysis**: Analyze images with Google Gemini vision models
- **Conversational AI**: Context-aware responses using Gemini or local Ollama models
- **Tool Execution Pipeline**: Iterative tool processing with limits to Prevent unintentional behavior.

### ✋ Hand Gesture Control
- Real-time hand tracking using MediaPipe and OpenCV
- Mouse control via hand movements
- Gesture-based clicks and actions

### 🌐 Connectivity & Information
- **Weather**: Real-time weather data via OpenWeatherMap
- **News**: RSS feed aggregation with Google News
- **Web Search**: SerpApi integration for Google search results
- **Wikipedia**: Quick topic summaries

### 📧 Communication & Automation
- **Email**: Send emails programmatically
- **WhatsApp**: Automated WhatsApp messaging
- **Task Scheduling**: Schedule tasks at specific times
- **Reminders**: Set time-based reminders with notifications
- **File Operations**: Copy, move, delete, search files

### 💻 Application Management
- Open and close applications by name
- Keyboard automation (typing, key presses)
- Clipboard operations (copy/paste)

## 📋 Prerequisites

- **Operating System**: Windows 10/11, macOS 12+, or modern Linux (Ubuntu 20.04+/Debian 11+ tested)
- **Python**: 3.10 or higher
- **Internet Connection**: Required for online features (Gemini API, TTS, weather, news)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Daniyal0100101/JARVIS-Autonomous-AI-Assistant.git
cd JARVIS-Autonomous-AI-Assistant
```

### 2. Install Dependencies

Use the installer. It prefers `Requirements/requirements.txt` and falls back to `requirements.txt`. It attempts bulk install and gracefully retries per package with guidance if needed.

```bash
python install_requirements.py
```

Tips for native deps:
- Windows: Install Microsoft C++ Build Tools when prompted.
- macOS: `brew install portaudio` (for PyAudio)
- Linux: `sudo apt install -y portaudio19-dev playerctl libsdl2-dev`

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Required for AI features
GEMINI_API_KEY=your_gemini_api_key_here

# Required for email functionality
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_app_specific_password

# Required for weather data
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Required for web search
SERPAPI_API_KEY=your_serpapi_key_here
```

**Getting API Keys:**
- **Gemini API**: [Google AI Studio](https://aistudio.google.com/app/api-keys)
- **OpenWeatherMap**: [OpenWeather API](https://openweathermap.org/api)
- **SerpApi**: [SerpApi Dashboard](https://serpapi.com/)

### 4. Set Up Authentication

Create `modules/password.py`:

```python
# modules/password.py
password = "your_secure_password_here"
```

**Security Note**: The password is hashed using SHA-256. Never commit this file to version control.

### 5. Configure Contacts (Optional)

Create `modules/contacts.py` for WhatsApp messaging:

```python
# modules/contacts.py
contacts = {
    "john": "+1234567890",
    "jane": "+0987654321",
    # Add more contacts as needed
}
```

## 🎯 Usage

### Starting Jarvis

```bash
python main.py
```

### Authentication

Upon launch, you'll be prompted to enter your password (3 attempts allowed). The password is securely masked during input.

### Command Modes

#### Voice Mode
- Speak naturally to Jarvis
- Requires online connectivity
- Automatically processes speech-to-text

#### Text Mode
- Type commands at the prompt
- Works offline for local operations
- Faster for precise commands

**Switch modes:**
```
"switch to voice mode"
"switch to text mode"
```

### Example Commands

```
# System Control
"lock the screen"
"increase volume"
"take a screenshot"
"shutdown in 10 minutes"

# Information
"what's the weather in Lahore?"
"get me the latest news"
"search for Python tutorials"
"tell me about quantum computing"

# File Operations
"create a directory called projects"
"search for config.json in Documents"
"copy file.txt to Desktop"

# Communication
"send an email to john@example.com"
"send a WhatsApp message to john"

# AI Features
"generate an image of a sunset over mountains"
"analyze the image on my desktop"

# Scheduling
"remind me to call mom at 3:30 PM"
"add a task at 09:00"
"show my tasks"

# Automation
"open calculator"
"close chrome"
"type Hello World"
```

## 🖥️ Cross‑Platform Notes

- Audio
  - Online TTS saves a temporary MP3 and plays it; files are written to the system temp directory with unique names and safely cleaned up.
  - Offline fallback uses `pyttsx3`.
  - Microphone input requires `PyAudio`.
- macOS
  - Some controls use AppleScript (Music play/pause, start screensaver for lock).
- Linux
  - Media control uses `playerctl` when installed.
  - Brightness tries `brightnessctl` or `xbacklight`.
  - For pygame audio, ensure SDL deps (`libsdl2-dev`).
- Windows
  - Lock screen uses `rundll32 user32.dll,LockWorkStation`.
  - Controlled Folder Access may block file I/O; use a normal writable folder.

## 🔧 Installer Behavior

- Prefers `Requirements/requirements.txt`; falls back to `requirements.txt`.
- Tries bulk install, then line‑by‑line with retries and OS‑specific hints.
- Runs `pip check` at the end to surface dependency conflicts.

## 🔧 Troubleshooting

- Permission denied when saving `*.mp3` during TTS
  - Cause: unwritable directory or file lock. Fix: now writes to temp directory with unique names and retries deletion.
- PyAudio install fails
  - macOS: `brew install portaudio` then `pip install PyAudio`.
  - Linux: `sudo apt install portaudio19-dev` then `pip install PyAudio`.
- Linux media/brightness controls do nothing
  - Install `playerctl`, `brightnessctl` or `xbacklight` as applicable.

## 🛠️ Architecture

### Tool Execution Pipeline

Jarvis uses an iterative tool execution system:

1. **Query Processing**: User input is analyzed by the AI model
2. **Tool Extraction**: AI generates `tool_code` blocks with function calls
3. **Validation**: Code is validated for security (AST parsing, whitelist checking)
4. **Execution**: Approved tools are executed in a sandboxed environment
5. **Feedback Loop**: Results feed back to the AI for up to 5 cycles
6. **Response Generation**: Final answer synthesized from tool results

### Security Features

- **Sandboxed Execution**: Only whitelisted functions can be called
- **AST Validation**: All tool code is parsed and validated before execution
- **No Arbitrary Code**: Only direct function calls with literal arguments allowed
- **Password Hashing**: SHA-256 hashing for authentication
- **Permission Checks**: System operations respect user permissions

## 📁 Project Structure

```
jarvis-ai-assistant/
│
├── main.py                          # Entry point
├── install_requirements.py          # Dependency installer
├── .env                            # Environment variables 
├── README.md                       # This file
├── LICENSE                         # MIT License
│
└── modules/
    ├── __init__.py
    ├── password.py                 # Authentication (create this)
    ├── contacts.py                 # Contact list (create this)
    ├── utils.py                    # Core utilities and tool pipeline
    ├── text_to_speech.py          # TTS functionality
    ├── speech_recognition.py      # STT functionality
    ├── system_control.py          # System operations
    ├── image_analysis.py          # Image analysis tools
    ├── image_generator.py         # Image generation tools
    ├── hand_gesture_detector.py   # Gesture control
    ├── apps_automation.py         # Email/WhatsApp automation
    ├── interrupt_handler.py       # Interrupt detection
```

## ⚙️ Configuration

### Customizing the AI Model

**Online Mode (Gemini)**:
Edit `utils.py` to change the model:
```python
gemini_model="gemini-2.5-flash"  # or "gemini-2.5-pro"
```

**Offline Mode (Ollama)**:
```python
model_name='gemma3'  # or 'llama3.2', 'mistral', etc.
```

### Tool Pipeline Settings

Adjust in `ToolExecutionPipeline` class:
```python
pipeline = ToolExecutionPipeline(
    max_tool_cycles=5,          # Maximum iteration cycles
    max_tools_per_cycle=3       # Tools per cycle
)
```

## 🔧 Troubleshooting

### Speech Recognition Issues
- Ensure microphone permissions are granted
- Check microphone is set as default input device
- Test with: `python -m speech_recognition`

### API Errors
- Verify API keys in `.env` file
- Check API rate limits and quotas
- Ensure internet connectivity for online features

### Import Errors
- Run `python install_requirements.py` again
- Manually install missing packages: `pip install package_name`
- Check Python version compatibility (3.10+)

### Hand Gesture Control Not Working
- Install latest OpenCV: `pip install opencv-python --upgrade`
- Ensure camera permissions are granted
- Test camera with: `python -c "import cv2; print(cv2.__version__)"`

## 🤝 Contributing

Contributions are welcome! Follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Commit** your changes: `git commit -m 'Add some feature'`
4. **Push** to the branch: `git push origin feature/your-feature-name`
5. **Open** a pull request

### Coding Standards
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include type hints where applicable
- Write comprehensive error handling

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Api.Airforce**: DALL-E 3 for image generation
- **Google**: Gemini AI models
- **OpenWeatherMap**: Weather data API
- **SerpApi**: Google search integration
- **MediaPipe**: Hand tracking technology

## 📞 Support

For issues, questions, or suggestions:
- **GitHub Issues**: [Open an issue](https://github.com/Daniyal0100101/JARVIS-Autonomous-AI-Assistant/issues)

## 🗺️ Roadmap

- [ ] Multi-language support
- [x] Cross-platform compatibility (macOS, Linux)
- [ ] Web interface with React frontend
- [ ] Voice customization options
- [ ] Plugin system for extensibility
- [ ] Cloud sync for conversation history
- [ ] Mobile companion app

---

**Built with ❤️ by [Daniyal](https://github.com/Daniyal0100101)**

*Star ⭐ this repository if you find it helpful!*
