# CJM
import json
import os
import requests
from pymongo import MongoClient
from datetime import datetime

# MongoDB connection settings (edit as needed)
MONGO_URI = 'mongodb+srv://TheTeleporter9:JTMdX9HFCllYRJDX@wro-scoring.n0khn.mongodb.net/?retryWrites=true&w=majority&appName=WRO-scoring'
DB_NAME = 'Wro-scoring'
COLLECTION_NAME = 'gamescores'
DISPLAY_COLLECTION = 'competition_display'
SCHEDULE_FILE = 'schedule.json'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
display_collection = db[DISPLAY_COLLECTION]

UPLOAD_URL = ''

def load_upload_url_from_settings(settings_path='settings.json'):
    """
    Loads the HTTP(S) server IP and port from the global settings JSON file,
    then builds and returns the full upload URL string.

    

    Args:
        settings_path (str): Path to your global settings JSON file.

    Returns:
        str: The constructed upload URL.
    """
    if not os.path.exists(settings_path):
        print(f"Settings file not found: {settings_path}")
        return 'http://127.0.0.1:5000/update'  # fallback URL

    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        ip_port = settings.get('https_server_ip', '127.0.0.1:5000')
        # Make sure the URL scheme is http or https as needed
        url = f'http://{ip_port}/update'
        return url
    except Exception as e:
        print(f"Failed to load settings or parse JSON: {e}")
        return 'http://127.0.0.1:5000/update'  # fallback URL


UPLOAD_URL = load_upload_url_from_settings()

def get_all_games():
    """
    Fetch all games from the MongoDB collection.
    Returns a list of game documents.
    """
    return list(collection.find())

def get_ranking_and_current_game():
    """
    Calculate team rankings and find the current game in progress.
    Returns (ranking, current_game)
    """
    games = list(collection.find())
    # Calculate ranking
    scores = {}
    for g in games:
        t1 = g.get('Team1', {})
        t2 = g.get('Team2', {})
        for t in [t1, t2]:
            name = t.get('Name')
            if name:
                scores[name] = scores.get(name, 0) + t.get('Score', 0)
    ranking = sorted(scores.items(), key=lambda x: x[1])  # Least points at top
    # Find game in progress (latest with status 'In Progress' or not played)
    current_game = None
    for g in sorted(games, key=lambda x: x.get('timestamp', ''), reverse=True):
        if g.get('status', '').lower() == 'in progress' or not g.get('status'):
            current_game = g
            break
    return ranking, current_game

def get_next_up_match_from_schedule():
    """
    Returns the next up match from the local schedule.json file.
    """
    if not os.path.exists(SCHEDULE_FILE):
        return None
    with open(SCHEDULE_FILE, 'r') as f:
        schedule = json.load(f)
    for match in schedule.get('matches', []):
        if match.get('next_up', False):
            return match
    return None

def publish_display_data():

    # CJM
    """
    Publish the next up match from the local schedule to an HTTPS endpoint.
    Synchronize scores if team names match, and send ranking instead of score.
    """
    next_up_match = get_next_up_match_from_schedule()
    # Load schedule for syncing
    schedule = None
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            schedule = json.load(f)
    # Sync scores if team names match
    if schedule:
        games = get_all_games()
        for match in schedule.get('matches', []):
            for game in games:
                t1 = game.get('Team1', {})
                t2 = game.get('Team2', {})
                if (match.get('team1') == t1.get('Name', '') and match.get('team2') == t2.get('Name', '')) or \
                   (match.get('team1') == t2.get('Name', '') and match.get('team2') == t1.get('Name', '')):
                    # Sync scores
                    if match.get('team1') == t1.get('Name', ''):
                        match['score1'] = t1.get('Score', 0)
                        match['score2'] = t2.get('Score', 0)
                    else:
                        match['score1'] = t2.get('Score', 0)
                        match['score2'] = t1.get('Score', 0)
        # Save back the updated schedule
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedule, f, indent=2)
    # Calculate rankings
    ranking, _ = get_ranking_and_current_game()
    # Map team name to rank (1-based, lowest score is best)
    ranking_sorted = sorted(ranking, key=lambda x: x[1])
    team_to_rank = {team: idx+1 for idx, (team, _) in enumerate(ranking_sorted)}
    if next_up_match:
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                schedule = json.load(f)
            match_number = str(schedule['matches'].index(next_up_match) + 1)
        except Exception:
            match_number = ''
        teamAName = next_up_match.get('team1', '')
        teamBName = next_up_match.get('team2', '')
        teamARank = team_to_rank.get(teamAName, 0)
        teamBRank = team_to_rank.get(teamBName, 0)

        print(teamARank)
        print(teamBRank)
    else:
        match_number = ''
        teamAName = ''
        teamARank = 0
        teamBName = ''
        teamBRank = 0

    payload = {
        'matchNumber': match_number,
        'tableNumber': 'Table 1',
        'teamAName': teamAName,
        'teamARank': teamARank,
        'teamBName': teamBName,
        'teamBRank': teamBRank
    }
    
    try:
        response = requests.post(UPLOAD_URL, json=payload)
        response.raise_for_status()
        print('Display data uploaded via HTTPS:', payload)
    except Exception as e:
        print('Error uploading display data via HTTPS:', e) 