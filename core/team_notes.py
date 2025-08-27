"""
Team notes functionality.
"""

import json

def save_team_notes(notes):
    """Save team notes to a file."""
    with open('team_notes.json', 'w') as f:
        json.dump(notes, f)

def load_team_notes():
    """Load team notes from file."""
    try:
        with open('team_notes.json', 'r') as f:
            return json.load(f)
    except:
        return {}
