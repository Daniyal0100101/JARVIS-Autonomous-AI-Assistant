# Jarvis AI Assistant

A "Jarvis-like" AI assistant for Windows, written in Python. It provides a rich, interactive command-line interface for controlling the system and accessing various AI-powered features. The assistant can be operated through both voice and text commands and includes a password-based authentication system.

## Core Functionalities

*   **Speech Recognition:** Utilizes the `faster-whisper` model for accurate and efficient speech-to-text transcription, enabling the assistant to understand spoken commands quickly and reliably.
*   **Text-to-Speech (TTS):** Employs the StreamElements API for high-quality online TTS and `pyttsx3` as an offline fallback.
*   **System Control:** Offers a wide range of system commands, including screen lock, volume and media control, brightness adjustment, and power options (shutdown, restart, log off). It can also capture screenshots and camera images.
*   **Application Automation:** Capable of sending WhatsApp messages and emails.
*   **AI-Powered Tools:**
    *   **Image Generation:** Generates images from text prompts using models like DALL-E 3.
    *   **Image Analysis:** Analyzes images using the Gemini model.
*   **Hand Gesture Control:** Uses `mediapipe` and `opencv-python` for mouse control and gesture-based actions like clicks and taking screenshots.
*   **Connectivity Awareness:** Automatically detects internet connectivity and adjusts its features accordingly (e.g., switching between online and offline TTS).

## Installation

The project has a significant number of dependencies. An installation script is provided to streamline the process.

```bash
python install_requirements.py
```

**Note:** Some packages may require manual installation steps as noted in `Requirements/requirements.txt`.

## Configuration

Before running the assistant, you need to configure the following:

*   **Environment Variables:** Create a `.env` file in the root directory with the following keys:
    *   `GEMINI_API_KEY`: Your API key for Google Gemini.
    *   `EMAIL_ADDRESS`: Your email address for sending emails.
    *   `EMAIL_PASSWORD`: Your email password.
    *   `OPENWEATHER_API_KEY`: Your API key for OpenWeatherMap.
    *   `SERPAPI_API_KEY`: Your API key for SerpApi (Google Search API).

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



## Execution

The main entry point of the application is `main.py`.

```bash
python main.py
```

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue on the GitHub repository.

If you want to contribute code, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
