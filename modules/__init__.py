import os

password = "Daniyal_pass"  # This will be used for authentication

# Contacts dictionary
contacts = {
    "mama" : "+923084122686",
    "papa" : "+971558150319",
    "natalia" : "+923124681701",
    "mariha" : "+923238833027"
    # Add more contacts as needed.
}

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