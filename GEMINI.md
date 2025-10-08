# Project Overview

This project is a "Jarvis-like" AI assistant for Windows, written in Python. It provides a rich, interactive command-line interface for controlling the system and accessing various AI-powered features. The assistant can be operated through both voice and text commands and includes a password-based authentication system.

## Core Functionalities

*   **Speech Recognition:** Utilizes the `faster-whisper` model for accurate speech-to-text transcription.
*   **Text-to-Speech (TTS):** Employs the StreamElements API for high-quality online TTS and `pyttsx3` as an offline fallback.
*   **System Control:** Offers a wide range of system commands, including screen lock, volume and media control, brightness adjustment, and power options (shutdown, restart, log off). It can also capture screenshots and camera images.
*   **Application Automation:** Capable of sending WhatsApp messages and emails.
*   **AI-Powered Tools:**
    *   **Image Generation:** Generates images from text prompts using models like DALL-E 3.
    *   **Image Analysis:** Analyzes images using the Gemini model.
*   **Hand Gesture Control:** Uses `mediapipe` and `opencv-python` for mouse control and gesture-based actions like clicks and taking screenshots.
*   **Connectivity Awareness:** Automatically detects internet connectivity and adjusts its features accordingly (e.g., switching between online and offline TTS).

# Building and Running

## 1. Installation

The project has a significant number of dependencies. An installation script is provided to streamline the process.

```bash
python install_requirements.py
```

**Note:** Some packages may require manual installation steps as noted in `Requirements/requirements.txt`.

## 2. Configuration

Before running the assistant, you need to configure the following:

*   **Environment Variables:** Create a `.env` file in the root directory with the following keys:
    *   `GEMINI_API_KEY`: Your API key for Google Gemini.
    *   `EMAIL_ADDRESS`: Your email address for sending emails.
    *   `EMAIL_PASSWORD`: Your email password.

*   **Password:** Create a `password.py` file in the `modules` directory and define a `password` variable with your desired password for authentication.

    ```python
    # modules/password.py
    password = "your_secret_password"
    ```

*   **Contacts:** Create a `contacts.py` file in the `modules` directory with a dictionary of contacts for sending WhatsApp messages.

    ```python
    # modules/contacts.py
    contacts = {
        "contact_name": "+1234567890",
        # Add more contacts here
    }
    ```

## 3. Execution

The main entry point of the application is `main.py`.

```bash
python main.py
```

# Development Conventions

*   **Modular Architecture:** The codebase is organized into modules located in the `modules/` directory, promoting separation of concerns.
*   **Modern CLI:** The `rich` library is used to create a visually appealing and user-friendly command-line interface.
*   **Configuration Management:** Environment variables are managed using the `dotenv` library, keeping sensitive information out of the source code.
*   **Error Handling:** The application includes error handling and provides informative feedback to the user.

# Coding pattern preferences

- Always prefer simple solutions
- Avoid duplication of code whenever possible, which means checking for other areas of the codebase that might already have similar code and functionality
- Write code that takes into account the different environments: dev, test, and prod
- You are careful to only make changes that are requested or you are confident are well understood and related to the change being requested
- When fixing an issue or bug, do not introduce a new pattern or technology without first exhausting all options for the existing implementation. And if you finally do this, make sure to remove the old implementation afterwards so we don't have duplicate logic.
- Keep the codebase very clean and organized
- Avoid writing scripts in files if possible, especially if the script is likely only to be run once
- Avoid having files over 200–300 lines of code. Refactor at that point.
- Mocking data is only needed for tests, never mock data for dev or prod
- Never add stubbing or fake data patterns to code that affects the dev or prod environments
- Never overwrite my .env file without first asking and confirming