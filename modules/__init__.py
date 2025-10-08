import os

# API keys path (relative to project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define constants
NOTE_FILE_PATH = "jarvis_notes.txt"

WORD_TO_OPERATOR = {
    '+': '+',
    '-': '-',
    'x': '*',
    '÷': '/'
}

# Initialize an empty conversation history
conversation_history = []

# List to store reminders
reminders = []