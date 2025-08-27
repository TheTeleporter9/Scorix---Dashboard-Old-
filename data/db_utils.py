"""
Database utilities for MongoDB operations.
"""
from datetime import datetime
from .mongodb_client import client, db, collection as main_collection, get_all_games

def get_db_collection(collection_name):
    """Get a MongoDB collection by name."""
    return db[collection_name]

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

def publish_display_data(match=None):
    """Publish data to display collection"""
    # Get the live announcements collection
    live_announce = get_db_collection('live_announcement')
    
    if match:
        match_data = match.copy()
        match_data['timestamp'] = datetime.now().isoformat()
        live_announce.delete_many({})
        live_announce.insert_one(match_data)
    else:
        # Get the next up match from schedule
        games = get_all_games()
        if games:
            latest_game = games[-1]
            latest_game['timestamp'] = datetime.now().isoformat()
            live_announce.delete_many({})
            live_announce.insert_one(latest_game)

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
