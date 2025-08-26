from core.match_scheduler import add_team, remove_team, set_num_matches, generate_round_robin, load_schedule, save_schedule, get_num_matches
import json

def add_team_to_schedule(team_name, randomize, schedule):
    """Add a team to the schedule"""
    if team_name.strip():
        add_team(schedule, team_name.strip(), randomize)
        return schedule
    return schedule

def remove_team_from_schedule(team_name, randomize, schedule):
    """Remove selected team from schedule"""
    remove_team(schedule, team_name, randomize)
    return schedule

def set_matches_per_team(num_matches, randomize, schedule):
    """Set number of matches per team"""
    if num_matches > 0:
        set_num_matches(schedule, num_matches, randomize)
        return schedule
    return schedule

def auto_generate_schedule(randomize, schedule):
    """Auto-generate round robin schedule"""
    num_matches = get_num_matches(schedule)
    schedule['matches'] = generate_round_robin(schedule['teams'], num_matches, randomize)
    return schedule

def get_teams_list(schedule):
    """Get list of teams from schedule"""
    return schedule.get('teams', [])

def save_team_notes(team_notes):
    """Save team notes to file"""
    with open('team_notes.json', 'w') as f:
        json.dump(team_notes, f, indent=2)

def load_team_notes():
    """Load team notes from file"""
    try:
        with open('team_notes.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {} 