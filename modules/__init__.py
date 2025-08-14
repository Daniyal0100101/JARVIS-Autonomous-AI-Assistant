import spacy
import os

# This file can be empty or can include initialization code if needed
password = "Daniyal_pass"  # This will be used for authentication

# Contacts dictionary
contacts = {
    "mama" : "+923084122686",
    "papa" : "+971558150319",
    "natalia sister" : "+923124681701",
    "mariha sister" : "+923238833027"
    # Add more contacts as needed
}

# API keys path (relative to project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EMAIL_CREDENTIALS_PATH = os.path.join(BASE_DIR, "Requirements", "email_credentials.txt")

# Define constants
NOTE_FILE_PATH = "notes.txt"

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

# Load spaCy model
nlp = spacy.load("en_core_web_sm")