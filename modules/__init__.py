import spacy

# This file can be empty or can include initialization code if needed
password = "Daniyal_pass"  # This will be used for authentication

# Contacts dictionary
contacts = {
    "daniyal" : "+923289287491",
    "mama" : "+923084122686",
    "papa" : "+971558150319",
    "natalia sister" : "+923124681701",
    "mariha sister" : "+923238833027"
    # Add more contacts as needed
}

# API keys path
WEATHER_API_KEY_PATH = r"C:\Users\DANIYAL\OneDrive\Documents\Program and Projacts\Hands-on Projects\AI Projacts\Jarvis AI Assistant\Requirements\weather api key.txt"
EMAIL_CREDENTIALS_PATH = r"C:\Users\DANIYAL\OneDrive\Documents\Program and Projacts\Hands-on Projects\AI Projacts\Jarvis AI Assistant\Requirements\email_credentials.txt"

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