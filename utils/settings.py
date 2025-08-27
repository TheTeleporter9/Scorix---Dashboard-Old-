"""Settings and configuration utilities."""
from typing import Dict, Any
import json

DEFAULT_SETTINGS: Dict[str, Any] = {
    'theme_color': '#e3f2fd',
    'default_matches_per_team': 1,
    'randomize_schedule': True,
    'dark_mode': False,
    'notification_sound': True,
    'font_size': 12,
    'highlight_color': '#FFEB3B',
    'auto_refresh_interval': 30,
    'display_update_interval': 30
}

def ensure_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required settings are present with defaults."""
    return {**DEFAULT_SETTINGS, **settings}

def load_settings() -> Dict[str, Any]:
    """Load settings from file with defaults."""
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            return ensure_settings(settings)
    except:
        return dict(DEFAULT_SETTINGS)

def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to file."""
    with open('settings.json', 'w') as f:
        json.dump(ensure_settings(settings), f)
