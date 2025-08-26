from data.mongodb_client import get_all_games, collection as main_collection
from core.tournament_logic import get_leaderboard
from datetime import datetime
import json

def sync_scores_from_mongodb(schedule):
    """Sync scores from MongoDB to schedule and update statuses"""
    games = get_all_games()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get next up match
    next_up_match = None
    for idx, match in enumerate(schedule.get('matches', [])):
        if match.get('next_up', False):
            next_up_match = idx
            break
    
    # Update matches with MongoDB data
    for idx, match in enumerate(schedule.get('matches', [])):
        team1 = match.get('team1', '')
        team2 = match.get('team2', '')
        
        # Find corresponding game in MongoDB
        for game in games:
            t1 = game.get('Team1', {})
            t2 = game.get('Team2', {})
            
            if (team1 == t1.get('Name', '') and team2 == t2.get('Name', '')) or \
               (team1 == t2.get('Name', '') and team2 == t1.get('Name', '')):
                
                # Check if scores have changed
                old_score1 = match.get('score1', 0)
                old_score2 = match.get('score2', 0)
                
                # Update scores
                if team1 == t1.get('Name', ''):
                    new_score1 = t1.get('Score', 0)
                    new_score2 = t2.get('Score', 0)
                    match['score1'] = new_score1
                    match['score2'] = new_score2
                    match['penalty_team1'] = t1.get('Penalty', False)
                    match['penalty_team2'] = t2.get('Penalty', False)
                else:
                    new_score1 = t2.get('Score', 0)
                    new_score2 = t1.get('Score', 0)
                    match['score1'] = new_score1
                    match['score2'] = new_score2
                    match['penalty_team1'] = t2.get('Penalty', False)
                    match['penalty_team2'] = t1.get('Penalty', False)
                
                # Add timestamp if scores changed
                if new_score1 != old_score1 or new_score2 != old_score2:
                    if 'score_history' not in match:
                        match['score_history'] = []
                    match['score_history'].append({
                        'timestamp': current_time,
                        'score1': new_score1,
                        'score2': new_score2,
                        'team1': team1,
                        'team2': team2
                    })
                
                # Update status based on rules
                if idx == next_up_match:
                    match['status'] = 'In Progress'
                elif match.get('score1', 0) > 0 or match.get('score2', 0) > 0:
                    match['status'] = 'Completed'
                    match['played'] = True
                else:
                    match['status'] = 'Not Started'
                    match['played'] = False
                
                break
    
    return schedule

def update_mongodb_from_schedule(schedule):
    """Update MongoDB with scores from schedule"""
    games = get_all_games()
    
    for match in schedule.get('matches', []):
        team1 = match.get('team1', '')
        team2 = match.get('team2', '')
        score1 = match.get('score1', 0)
        score2 = match.get('score2', 0)
        
        # Find and update corresponding game in MongoDB
        for game in games:
            t1 = game.get('Team1', {})
            t2 = game.get('Team2', {})
            
            if (team1 == t1.get('Name', '') and team2 == t2.get('Name', '')) or \
               (team1 == t2.get('Name', '') and team2 == t1.get('Name', '')):
                
                # Update the game document
                if team1 == t1.get('Name', ''):
                    game['Team1']['Score'] = score1
                    game['Team2']['Score'] = score2
                else:
                    game['Team1']['Score'] = score2
                    game['Team2']['Score'] = score1
                
                # Update in MongoDB
                main_collection.update_one(
                    {'_id': game['_id']},
                    {'$set': game}
                )
                break

def get_all_teams_from_schedule_and_games(schedule):
    """Get all teams that appear in both schedule and games"""
    teams = set()
    
    # Add teams from schedule
    for match in schedule.get('matches', []):
        teams.add(match.get('team1', ''))
        teams.add(match.get('team2', ''))
    
    # Add teams from MongoDB games
    games = get_all_games()
    for game in games:
        t1 = game.get('Team1', {})
        t2 = game.get('Team2', {})
        teams.add(t1.get('Name', ''))
        teams.add(t2.get('Name', ''))
    
    return list(teams)

def get_team_scores_for_finals(schedule):
    """Get team scores for finals, only including teams that appear in games tab"""
    teams = get_all_teams_from_schedule_and_games(schedule)
    games = get_all_games()
    
    # Calculate scores for each team
    team_scores = {}
    for team in teams:
        if team:  # Skip empty team names
            team_scores[team] = 0
    
    # Sum up scores from MongoDB games
    for game in games:
        t1 = game.get('Team1', {})
        t2 = game.get('Team2', {})
        team1_name = t1.get('Name', '')
        team2_name = t2.get('Name', '')
        
        if team1_name in team_scores:
            team_scores[team1_name] += t1.get('Score', 0)
        if team2_name in team_scores:
            team_scores[team2_name] += t2.get('Score', 0)
    
    # Convert to list and sort by score (lowest first for finals)
    team_list = [{'team': team, 'score': score} for team, score in team_scores.items()]
    team_list.sort(key=lambda x: x['score'])
    
    return team_list[:4]  # Return top 4 teams with lowest scores 