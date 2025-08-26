import json
import os
from itertools import combinations
import random

SCHEDULE_FILE = 'schedule.json'

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

def add_team(schedule, team_name, randomize=True):
    if team_name not in schedule['teams']:
        schedule['teams'].append(team_name)
        schedule['matches'] = generate_round_robin(schedule['teams'], get_num_matches(schedule), randomize)

def remove_team(schedule, team_name, randomize=True):
    if team_name in schedule['teams']:
        schedule['teams'].remove(team_name)
        schedule['matches'] = generate_round_robin(schedule['teams'], get_num_matches(schedule), randomize)

def get_num_matches(schedule):
    if not schedule['matches']:
        return 1
    teams = schedule['teams']
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