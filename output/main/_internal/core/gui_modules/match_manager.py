from core.match_scheduler import (
    get_match, set_match_played, set_match_penalty, 
    set_match_comment, get_match_comment, load_schedule, save_schedule
)
from data.mongodb_client import collection as main_collection
from pymongo import MongoClient
import json

MATCH_STATUSES = ['Not Started', 'In Progress', 'Completed', 'Disqualified']
REFEREES = ['Referee 1', 'Referee 2', 'Referee 3', 'Referee 4']

def get_match_data(match_id, schedule):
    """Get match data by ID"""
    return get_match(schedule, match_id)

def set_match_status(match_id, status, schedule):
    """Set match status"""
    if status in MATCH_STATUSES:
        set_match_played(schedule, match_id, status == 'Completed')
        return True
    return False

def set_match_penalty_for_team(match_id, team, penalty, schedule):
    """Set penalty for a team in a match"""
    set_match_penalty(schedule, match_id, team, penalty)
    return True

def set_match_referee(match_id, referee):
    """Set referee for a match"""
    if referee in REFEREES:
        # This would need to be implemented in match_scheduler
        # For now, we'll update the schedule directly
        schedule = load_schedule()
        if match_id < len(schedule['matches']):
            schedule['matches'][match_id]['referee'] = referee
            save_schedule(schedule)
        return True
    return False

def set_match_scores(match_id, score1, score2):
    """Set scores for a match"""
    # This would need to be implemented in match_scheduler
    # For now, we'll update the schedule directly
    schedule = load_schedule()
    if match_id < len(schedule['matches']):
        schedule['matches'][match_id]['score1'] = score1
        schedule['matches'][match_id]['score2'] = score2
        save_schedule(schedule)
    return True

def set_next_up_match(match_id):
    """Set a match as next up"""
    # Clear all next_up flags first
    schedule = load_schedule()
    for match in schedule['matches']:
        match['next_up'] = False
    
    # Set the selected match as next up
    if match_id < len(schedule['matches']):
        schedule['matches'][match_id]['next_up'] = True
        save_schedule(schedule)
    return True

def get_matches_list(schedule):
    """Get list of matches from schedule"""
    return schedule.get('matches', [])

def save_schedule_to_file(schedule, show_popup=True):
    """Save schedule to file"""
    save_schedule(schedule)
    return True

def load_schedule_from_file():
    """Load schedule from file"""
    return load_schedule()

def get_next_up_match_from_schedule(schedule):
    """Get the next up match from schedule"""
    for i, match in enumerate(schedule.get('matches', [])):
        if match.get('next_up', False):
            return i, match
    return None, None

def set_match_comment_data(match_id, comment, schedule):
    """Set comment for a match"""
    set_match_comment(schedule, match_id, comment)
    return True

def get_match_comment_data(match_id, schedule):
    """Get comment for a match"""
    return get_match_comment(schedule, match_id) 