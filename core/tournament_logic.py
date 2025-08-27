from collections import defaultdict
from core.match_scheduler import (
    load_schedule, save_schedule, get_match, set_match_played,
    add_team, remove_team, get_num_matches, generate_round_robin
)

def get_next_game(games):
    """
    Determines the next game number based on the highest played game.
    """
    played_numbers = []
    for g in games:
        val = g.get('GameNumber', None)
        try:
            num = int(val)
            played_numbers.append(num)
        except (TypeError, ValueError):
            continue
    if not played_numbers:
        return 1
    return max(played_numbers) + 1


def get_leaderboard(games):
    """
    Returns a sorted list of (team_name, total_score) tuples.
    """
    scores = defaultdict(int)
    for g in games:
        t1 = g.get('Team1', {})
        t2 = g.get('Team2', {})
        if 'Name' in t1 and 'Score' in t1:
            scores[t1['Name']] += t1['Score']
        if 'Name' in t2 and 'Score' in t2:
            scores[t2['Name']] += t2['Score']
    leaderboard = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return leaderboard 


def get_match_data(idx, schedule):
    if 0 <= idx < len(schedule['matches']):
        return schedule['matches'][idx]
    return None

def add_team_to_schedule(team_name, randomize, schedule):
    add_team(schedule, team_name, randomize)
    return schedule

def remove_team_from_schedule(team_name, randomize, schedule):
    remove_team(schedule, team_name, randomize)
    return schedule

def set_matches_per_team(num, randomize, schedule):
    old_num = get_num_matches(schedule)
    if old_num != num:
        schedule['matches'] = generate_round_robin(schedule['teams'], num, randomize)
    return schedule

def auto_generate_schedule(randomize, schedule):
    num_matches = get_num_matches(schedule)
    schedule['matches'] = generate_round_robin(schedule['teams'], num_matches, randomize)
    return schedule

def refresh_tournament_data():
    """Gets fresh tournament data from the database."""
    from data.mongodb_client import collection
    data = list(collection.find())
    return {'games': data} if data else {'games': []}

def set_match_penalty_for_team(idx, team_num, penalty_value, schedule):
    """Set penalty for a specific team in a match.
    team_num should be 1 or 2."""
    if 0 <= idx < len(schedule['matches']):
        match = schedule['matches'][idx]
        if team_num == 1:
            match['penalty_team1'] = penalty_value
        elif team_num == 2:
            match['penalty_team2'] = penalty_value
    return schedule

def get_team_scores_for_finals(games):
    """Calculate total scores for teams to determine finals qualification"""
    team_scores = {}
    for g in games:
        t1, t2 = g.get('Team1', {}), g.get('Team2', {})
        for team in [t1, t2]:
            name = team.get('Name', '')
            if name:
                score = int(team.get('Score', 0))
                if name not in team_scores:
                    team_scores[name] = {'total': 0, 'games': 0}
                team_scores[name]['total'] += score
                team_scores[name]['games'] += 1
    
    # Calculate averages and sort
    scored = []
    for team, data in team_scores.items():
        if data['games'] > 0:  # Only include teams that played
            avg = data['total'] / data['games']
            scored.append((team, avg))
    
    return sorted(scored, key=lambda x: x[1], reverse=True)

def create_finals_schedule(top_teams):
    """Create finals matches for top teams"""
    if len(top_teams) < 4:
        return []
    
    # Semi-finals
    semifinals = [
        {
            'round': 'semifinal',
            'number': 1,
            'team1': top_teams[0][0],
            'team2': top_teams[3][0],
            'played': False
        },
        {
            'round': 'semifinal',
            'number': 2,
            'team1': top_teams[1][0],
            'team2': top_teams[2][0],
            'played': False
        }
    ]
    
    # Finals placeholders
    finals = [
        {
            'round': 'final',
            'number': 1,
            'team1': '',
            'team2': '',
            'played': False
        },
        {
            'round': 'third',
            'number': 2,
            'team1': '',
            'team2': '',
            'played': False
        }
    ]
    
    return semifinals + finals

def get_match_comment_data(idx, schedule):
    """Get comment for a match"""
    if 0 <= idx < len(schedule['matches']):
        return schedule['matches'][idx].get('comments', '')
    return ''

def add_comment_to_history(idx, comment, timestamp, schedule):
    """Add a comment to match history"""
    if 0 <= idx < len(schedule['matches']):
        match = schedule['matches'][idx]
        if 'comment_history' not in match:
            match['comment_history'] = []
        match['comment_history'].append({
            'comment': comment,
            'timestamp': timestamp
        })