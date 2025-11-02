"""Jarvis modules package-level constants and shared stores.

This module keeps lightweight configuration and in-memory data shared across
the assistant. Heavy imports are avoided here to keep startup fast.

Attributes:
- NOTE_FILE_PATH: Default path for quick notes saved by Jarvis.
- WORD_TO_OPERATOR: Mapping of spoken math tokens to Python operators.
- conversation_history: In-memory log of recent user/assistant exchanges.
- reminders: In-memory collection of scheduled reminders.
"""

import os

# API keys path (relative to project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Default file used by note-taking helpers
NOTE_FILE_PATH = "jarvis_notes.txt"

# Map common spoken math tokens to operators (used by secure evaluation)
WORD_TO_OPERATOR = {
    '+': '+',
    '-': '-',
    'x': '*',
    '/': '/',  # fixed previously garbled character
}

# Store the conversation history in a list
conversation_history = []

# List to store reminders
reminders = []