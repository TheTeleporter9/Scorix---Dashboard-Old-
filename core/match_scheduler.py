import json
import os
from itertools import combinations
import random

"""Match scheduler with type hints."""

from typing import Dict, List, Union, Any, Optional, TypedDict
from datetime import datetime
import random
import os
import json

SCHEDULE_FILE = 'schedule.json'

# Type definitions
class MatchComment(TypedDict):
    comment: str
    timestamp: str

class Match(TypedDict):
    team1: str
    team2: str
    played: bool
    penalty_team1: bool
    penalty_team2: bool
    comments: str
    comment_history: List[MatchComment]
    created: str

class Schedule(TypedDict):
    teams: List[str]
    matches: List[Match]

__all__ = [
    'MatchComment', 'Match', 'Schedule',
    'load_schedule', 'save_schedule',
    'add_team', 'remove_team',
    'get_match_data', 'set_match_played',
    'set_match_comment_data', 'get_match_comment_data',
    'add_comment_to_history'
]

# Match Status Constants
MATCH_STATUSES = [
    'Not Played',
    'Waiting',
    'In Progress',
    'Completed',
    'Cancelled',
    'Postponed'
]

def load_schedule():
    """Load the schedule from file. If invalid or missing, return an empty schedule."""
    if not os.path.exists(SCHEDULE_FILE):
        return {'teams': [], 'matches': []}

    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[WARNING] schedule.json is invalid or corrupted at line {e.lineno}, column {e.colno}: {e.msg}")
            print("[INFO] Returning a fresh empty schedule.")
            return {'teams': [], 'matches': []}

def save_schedule(schedule):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f, indent=2)

def generate_round_robin(teams, num_matches=1, randomize=True):
    matches = []
    for _ in range(num_matches):
        for t1, t2 in combinations(teams, 2):
            matches.append({'team1': t1, 'team2': t2, 'played': False, 'penalty_team1': False, 'penalty_team2': False, 'comments': '', 'comment_history': []})
    if randomize and num_matches > 2:
        random.shuffle(matches)
    return matches

def add_team(team_name, schedule, randomize=True):
    """Add a team to the schedule"""
    if not isinstance(schedule, dict):
        schedule = load_schedule()
    if team_name not in schedule.get('teams', []):
        if 'teams' not in schedule:
            schedule['teams'] = []
        schedule['teams'].append(team_name)
        num_matches = len(schedule.get('matches', [])) // (len(schedule['teams']) * (len(schedule['teams']) - 1) // 2) if len(schedule['teams']) > 1 else 1
        schedule['matches'] = generate_round_robin(schedule['teams'], num_matches, randomize)
        save_schedule(schedule)

def remove_team(team_name, schedule, randomize=True):
    """Remove a team from the schedule"""
    if not isinstance(schedule, dict):
        schedule = load_schedule()
    if 'teams' not in schedule:
        schedule['teams'] = []
    if team_name in schedule['teams']:
        schedule['teams'].remove(team_name)
        num_matches = len(schedule.get('matches', [])) // (len(schedule['teams']) * (len(schedule['teams']) - 1) // 2) if len(schedule['teams']) > 1 else 1
        schedule['matches'] = generate_round_robin(schedule['teams'], num_matches, randomize)
        save_schedule(schedule)

def set_match_comment_data(idx, comment, schedule):
    """Set comment for a match"""
    if 0 <= idx < len(schedule['matches']):
        schedule['matches'][idx]['comments'] = comment
        save_schedule(schedule)

def set_match_played(schedule: Schedule, idx: int, played: bool) -> None: # type: ignore
    """Set whether a match has been played"""
    if 0 <= idx < len(schedule['matches']):
        schedule['matches'][idx]['played'] = played
        save_schedule(schedule)

def get_match_data(idx, schedule):
    """Get match data by index"""
    if 0 <= idx < len(schedule['matches']):
        return schedule['matches'][idx]
    return None

def get_match_comment_data(idx, schedule):
    """Get comment for a match."""
    if 0 <= idx < len(schedule['matches']):
        return schedule['matches'][idx].get('comments', '')
    return ''

def add_comment_to_history(idx, comment, timestamp, schedule):
    """Add a comment to match history."""
    if 0 <= idx < len(schedule['matches']):
        history = schedule['matches'][idx].get('comment_history', [])
        history.append({
            'comment': comment,
            'timestamp': timestamp
        })
        schedule['matches'][idx]['comment_history'] = history
        save_schedule(schedule)

def get_num_matches(schedule):
    if not schedule['matches']:
        return 1
    teams = schedule['teams']
    if not teams:
        return 1
    n = len([m for m in schedule['matches'] if m['team1'] == teams[0]])
    return max(1, n)

def set_num_matches(schedule, num_matches, randomize=True):
    schedule['matches'] = generate_round_robin(schedule['teams'], num_matches, randomize)

def get_match(schedule, idx):
    return schedule['matches'][idx]

def set_match_played(schedule, idx, played):
    schedule['matches'][idx]['played'] = played

def set_match_penalty(schedule, idx, team, penalty):
    if team == 1:
        schedule['matches'][idx]['penalty_team1'] = penalty
    elif team == 2:
        schedule['matches'][idx]['penalty_team2'] = penalty

def set_match_comment(schedule, idx, comment):
    if 'comment_history' not in schedule['matches'][idx]:
        schedule['matches'][idx]['comment_history'] = []
    schedule['matches'][idx]['comments'] = comment

def get_match_comment(schedule, idx):
    return schedule['matches'][idx].get('comments', '') 