# CJM
from data.mongodb_client import get_all_games, collection as main_collection
from core.tournament_logic import get_leaderboard
import json

def get_top_teams_for_finals(num_teams=4):
    # CJM
    """Get top teams for finals bracket"""
    games = get_all_games()
    scores = {}
    for g in games:
        t1 = g.get('Team1', {})
        t2 = g.get('Team2', {})
        scores[t1.get('Name', '')] = scores.get(t1.get('Name', ''), 0) + t1.get('Score', 0)
        scores[t2.get('Name', '')] = scores.get(t2.get('Name', ''), 0) + t2.get('Score', 0)
    top_teams = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:num_teams]
    return [{'team': team, 'score': score} for team, score in top_teams]

def create_finals_schedule(top_teams):
    """Create finals bracket schedule"""
    if len(top_teams) < 4:
        return None
    
    # Create semifinal matches
    semifinal1 = {
        'team1': top_teams[0]['team'],
        'team2': top_teams[3]['team'],
        'status': 'Not Started',
        'winner': None
    }
    
    semifinal2 = {
        'team1': top_teams[1]['team'],
        'team2': top_teams[2]['team'],
        'status': 'Not Started',
        'winner': None
    }
    
    # Create final and third place matches (initially empty)
    final_match = {
        'team1': '',
        'team2': '',
        'status': 'Not Started',
        'winner': None
    }
    
    third_place = {
        'team1': '',
        'team2': '',
        'status': 'Not Started',
        'winner': None
    }
    
    finals_schedule = {
        'semifinals': [semifinal1, semifinal2],
        'final': final_match,
        'third_place': third_place,
        'champion': None,
        'runner_up': None,
        'third_place_team': None
    }
    
    return finals_schedule

def set_finals_match_winner(match_type, match_index, winner, finals_schedule):
    """Set winner for a finals match"""
    if match_type == 'semifinal':
        if match_index < len(finals_schedule['semifinals']):
            finals_schedule['semifinals'][match_index]['winner'] = winner
            finals_schedule['semifinals'][match_index]['status'] = 'Completed'
            
            # Update final match if both semifinals are complete
            completed_semifinals = [m for m in finals_schedule['semifinals'] if m['status'] == 'Completed']
            if len(completed_semifinals) == 2:
                winners = [m['winner'] for m in completed_semifinals]
                losers = []
                for semifinal in finals_schedule['semifinals']:
                    if semifinal['team1'] != semifinal['winner']:
                        losers.append(semifinal['team1'])
                    else:
                        losers.append(semifinal['team2'])
                
                finals_schedule['final']['team1'] = winners[0]
                finals_schedule['final']['team2'] = winners[1]
                finals_schedule['third_place']['team1'] = losers[0]
                finals_schedule['third_place']['team2'] = losers[1]
    
    elif match_type == 'final':
        finals_schedule['final']['winner'] = winner
        finals_schedule['final']['status'] = 'Completed'
        finals_schedule['champion'] = winner
        # Set runner up
        if finals_schedule['final']['team1'] == winner:
            finals_schedule['runner_up'] = finals_schedule['final']['team2']
        else:
            finals_schedule['runner_up'] = finals_schedule['final']['team1']
    
    elif match_type == 'third_place':
        finals_schedule['third_place']['winner'] = winner
        finals_schedule['third_place']['status'] = 'Completed'
        finals_schedule['third_place_team'] = winner
    
    return finals_schedule

def save_finals_schedule(finals_schedule):
    """Save finals schedule to file"""
    with open('finals_schedule.json', 'w') as f:
        json.dump(finals_schedule, f, indent=2)
    return True

def load_finals_schedule():
    """Load finals schedule from file"""
    try:
        with open('finals_schedule.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None 