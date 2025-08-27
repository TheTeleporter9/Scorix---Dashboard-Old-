"""Match scheduler core functions."""
from typing import Dict, List, Union, Optional
import random
import os
import json
from datetime import datetime

SCHEDULE_FILE = 'schedule.json'

# Type hints
Schedule = Dict[str, Union[List[str], List[Dict]]]
Match = Dict[str, Union[str, bool, List, Dict]]

def load_schedule() -> Schedule:
    """Load schedule from file, return empty if not found"""
    if not os.path.exists(SCHEDULE_FILE):
        return {'teams': [], 'matches': []}
        
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {'teams': [], 'matches': []}

def save_schedule(schedule: Schedule) -> None:
    """Save schedule to file"""
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f, indent=2)

def generate_round_robin(teams: List[str], num_matches: int = 1, randomize: bool = True) -> List[Match]:
    """Generate round robin matches for teams"""
    matches = []
    for _ in range(num_matches):
        for i, t1 in enumerate(teams[:-1]):
            for j, t2 in enumerate(teams[i+1:], i+1):
                matches.append({
                    'team1': t1, 
                    'team2': t2,
                    'played': False, 
                    'penalty_team1': False,
                    'penalty_team2': False,
                    'comments': '',
                    'comment_history': [],
                    'created': datetime.now().isoformat()
                })
    if randomize:
        random.shuffle(matches)
    return matches

def add_team(schedule: Schedule, team_name: str, randomize: bool = True) -> None:
    """Add a team to the schedule"""
    if team_name not in schedule['teams']:
        schedule['teams'].append(team_name)
        num_matches = get_num_matches(schedule)
        schedule['matches'] = generate_round_robin(schedule['teams'], num_matches, randomize)
        save_schedule(schedule)

def remove_team(schedule: Schedule, team_name: str, randomize: bool = True) -> None:
    """Remove a team from the schedule"""
    if team_name in schedule['teams']:
        schedule['teams'].remove(team_name)
        num_matches = get_num_matches(schedule)
        schedule['matches'] = generate_round_robin(schedule['teams'], num_matches, randomize)
        save_schedule(schedule)

def get_num_matches(schedule: Schedule) -> int:
    """Get the number of matches per team"""
    if not schedule['matches'] or not schedule['teams']:
        return 1
    matches_with_first_team = [m for m in schedule['matches'] if m['team1'] == schedule['teams'][0]]
    return len(matches_with_first_team) or 1

def set_match_comment_data(idx: int, comment: str, schedule: Schedule) -> None:
    """Set comment for a match"""
    if 0 <= idx < len(schedule['matches']):
        schedule['matches'][idx]['comments'] = comment
        save_schedule(schedule)

def get_match_comment_data(idx: int, schedule: Schedule) -> str:
    """Get comment for a match"""
    if 0 <= idx < len(schedule['matches']):
        return schedule['matches'][idx].get('comments', '')
    return ''

def add_comment_to_history(idx: int, comment: str, timestamp: str, schedule: Schedule) -> None:
    """Add a comment to match history"""
    if 0 <= idx < len(schedule['matches']):
        match = schedule['matches'][idx]
        if 'comment_history' not in match:
            match['comment_history'] = []
        match['comment_history'].append({
            'comment': comment,
            'timestamp': timestamp
        })
        save_schedule(schedule)

def set_match_played(schedule: Schedule, idx: int, played: bool) -> None:
    """Set whether a match has been played"""
    if 0 <= idx < len(schedule['matches']):
        schedule['matches'][idx]['played'] = played
        save_schedule(schedule)

def get_match_data(idx: int, schedule: Schedule) -> Optional[Match]:
    """Get match data by index"""
    if 0 <= idx < len(schedule['matches']):
        return schedule['matches'][idx]
    return None
