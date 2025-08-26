import json
import os

SETTINGS_FILE = 'settings.json'
DEFAULT_SETTINGS = {
    'theme_color': '#e3f2fd',
    'default_matches_per_team': 1,
    'randomize_schedule': True
}

COMP_DISPLAY_SETTINGS_FILE = 'competition_display_settings.json'

def load_settings():
    """Load settings from file or return defaults"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def load_comp_display_settings():
    """Load competition display settings"""
    if os.path.exists(COMP_DISPLAY_SETTINGS_FILE):
        with open(COMP_DISPLAY_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {
        'DISPLAY_MONGO_URI': 'mongodb://localhost:27017/',
        'DISPLAY_DB_NAME': 'tournament_db',
        'DISPLAY_COLLECTION_NAME': 'competition_display',
    }

def save_comp_display_settings(settings):
    """Save competition display settings"""
    with open(COMP_DISPLAY_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2) 