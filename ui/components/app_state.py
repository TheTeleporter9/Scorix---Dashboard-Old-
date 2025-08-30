"""
Application state and shared functionality.
"""

import json
from typing import Dict, List, Any, Optional, Union, TypedDict, cast
from datetime import datetime
import tkinter as tk
from data.db_utils import (
    get_all_games, get_db_collection, sync_scores_from_mongodb,
    update_mongodb_from_schedule, publish_display_data,
    get_all_teams_from_schedule_and_games
)
from core.match_scheduler import (
    load_schedule, save_schedule, add_team, remove_team,
    generate_round_robin, get_match_data as get_match, set_match_played,
    set_match_comment_data as set_match_comment, get_match_comment_data as get_match_comment,
    add_comment_to_history, Schedule
)
from core.team_notes import save_team_notes, load_team_notes
from utils.type_utils import ensure_dict

class Settings(TypedDict, total=True):
    """TypedDict for application settings.
    All fields are required and have defaults in utils.settings.
    """
    theme_color: str
    default_matches_per_team: int
    randomize_schedule: bool
    dark_mode: bool
    notification_sound: bool
    font_size: int
    highlight_color: str
    auto_refresh_interval: int
    display_update_interval: int

from utils.settings import load_settings as load_settings_with_defaults

class AppState:
    def __init__(self):
        self._schedule: Schedule = ensure_dict(load_schedule(), Schedule)
        settings_dict = load_settings_with_defaults()
        self._settings: Settings = cast(Settings, ensure_dict(settings_dict, Settings))
        self.tournament_data: List[Dict[str, Any]] = []
        self.finals_data: Optional[Dict[str, Any]] = None
        
        # Use the default interval from settings
        self.display_update_interval: int = self._settings['display_update_interval'] * 1000  # ms
        self.display_update_job: Optional[Any] = None
        self.auto_refresh_enabled: bool = True
        self.auto_refresh_interval: int = self._settings['auto_refresh_interval']  # seconds
        self.root: Optional[tk.Tk] = None
    
    @property
    def settings(self) -> Settings:
        """Safe access to settings with defaults."""
        return self._settings
    
    @settings.setter
    def settings(self, value: Dict[str, Any]) -> None:
        self._settings = ensure_dict(value, Settings)
    
    @property
    def schedule(self) -> Schedule:
        """Safe access to schedule."""
        return self._schedule
    
    @schedule.setter
    def schedule(self, value: Dict[str, Any]) -> None:
        self._schedule = ensure_dict(value, Schedule)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Safely get a setting value with a default."""
        return self.settings.get(key, default)

    def apply_theme(self) -> None:
        """Apply the current theme settings to the UI"""
        if not self.root:
            return
        
        theme_color = self.settings.get('theme_color', '#e3f2fd')
        is_dark = self.settings.get('dark_mode', False)
        highlight_color = self.settings.get('highlight_color', '#2196f3')
        
        bg_color = '#2c2c2c' if is_dark else theme_color
        fg_color = 'white' if is_dark else 'black'
        
        # Apply to root window and all children
        for widget in [self.root] + list(self.root.winfo_children()):
            try:
                widget.configure(bg=bg_color)
                if hasattr(widget, 'configure'):
                    if 'foreground' in widget.configure():
                        widget.configure(fg=fg_color)
                    if 'selectbackground' in widget.configure():
                        widget.configure(selectbackground=highlight_color)
                    if 'selectforeground' in widget.configure():
                        widget.configure(selectforeground='white')
            except tk.TclError:
                # Some widgets might not support all configurations
                pass

def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {'theme_color': '#e3f2fd', 'default_matches_per_team': 1, 'randomize_schedule': True}

def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

def load_comp_display_settings():
    try:
        with open('display_settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            'DISPLAY_MONGO_URI': '',
            'DISPLAY_DB_NAME': '',
            'DISPLAY_COLLECTION_NAME': ''
        }

def save_comp_display_settings(settings):
    with open('display_settings.json', 'w') as f:
        json.dump(settings, f)

def update_mongodb_from_schedule(schedule):
    """Update MongoDB with the latest schedule data"""
    if not schedule:
        return
    for match in schedule['matches']:
        if match.get('played'):
            # Format data for MongoDB
            game_data = {
                'GameNumber': match.get('match_id', ''),
                'timestamp': datetime.now().isoformat(),
                'Team1': {
                    'Name': match['team1'],
                    'Score': match.get('score1', 0)
                },
                'Team2': {
                    'Name': match['team2'],
                    'Score': match.get('score2', 0)
                }
            }
            collection = get_db_collection('gamescores')
            collection.update_one(
                {'GameNumber': match.get('match_id')},
                {'$set': game_data},
                upsert=True
            )

def sync_scores_from_mongodb(schedule):
    """Sync scores from MongoDB to schedule"""
    if not schedule:
        return schedule
    
    games = get_all_games()
    for match in schedule['matches']:
        for game in games:
            if (match['team1'] == game.get('Team1', {}).get('Name') and 
                match['team2'] == game.get('Team2', {}).get('Name')):
                match['score1'] = game['Team1'].get('Score', 0)
                match['score2'] = game['Team2'].get('Score', 0)
                if not match.get('score_history'):
                    match['score_history'] = []
                match['score_history'].append({
                    'team1': match['team1'],
                    'team2': match['team2'],
                    'score1': match['score1'],
                    'score2': match['score2'],
                    'timestamp': game.get('timestamp', datetime.now().isoformat())
                })
    return schedule

def get_all_teams_from_schedule_and_games(schedule):
    """Get all teams that appear in both schedule and games"""
    teams = set()
    if schedule and schedule.get('teams'):
        teams.update(schedule['teams'])
    games = get_all_games()
    for game in games:
        if 'Team1' in game and 'Name' in game['Team1']:
            teams.add(game['Team1']['Name'])
        if 'Team2' in game and 'Name' in game['Team2']:
            teams.add(game['Team2']['Name'])
    return sorted(list(teams))
