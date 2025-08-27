"""
Application state and shared functionality.
"""

import json
from datetime import datetime
from data.mongodb_client import get_all_games, collection as main_collection
from core.match_scheduler import (
    load_schedule, save_schedule, add_team, remove_team, set_num_matches,
    generate_round_robin, get_match, set_match_played, set_match_penalty,
    set_match_comment, get_match_comment
)
from core.team_notes import save_team_notes, load_team_notes

# Add a new MongoDB collection for live announcements
LIVE_ANNOUNCE_COLLECTION = 'live_announcement'
live_announce_collection = main_collection.database[LIVE_ANNOUNCE_COLLECTION]

class AppState:
    def __init__(self):
        self.schedule = {}
        self.settings = {}
        self.display_update_interval = 30 * 1000  # 30 seconds
        self.display_update_job = None
        self.auto_refresh_enabled = True
        self.auto_refresh_interval = 30  # seconds

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
            main_collection.update_one(
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
