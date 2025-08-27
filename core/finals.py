"""
Tournament finals functionality.
"""

def get_team_scores_for_finals(schedule):
    """Get the top teams with their scores for finals setup."""
    if not schedule or not schedule.get('matches'):
        return []
    
    team_scores = {}
    for match in schedule['matches']:
        if match.get('played'):
            team1 = match['team1']
            team2 = match['team2']
            if team1 not in team_scores:
                team_scores[team1] = {'team': team1, 'score': 0}
            if team2 not in team_scores:
                team_scores[team2] = {'team': team2, 'score': 0}
            team_scores[team1]['score'] += match.get('score1', 0)
            team_scores[team2]['score'] += match.get('score2', 0)
    
    # Sort teams by score and return top 4
    teams_list = list(team_scores.values())
    teams_list.sort(key=lambda x: x['score'], reverse=True)
    return teams_list[:4]

def create_finals_schedule(top_teams):
    """Create a finals bracket with semi-finals and finals matches."""
    if len(top_teams) < 4:
        return None
    
    # Create semifinal matches
    semifinals = [
        {
            'round': 'semifinal',
            'team1': top_teams[0]['team'],
            'team2': top_teams[3]['team'],
            'played': False,
            'score1': 0,
            'score2': 0
        },
        {
            'round': 'semifinal',
            'team1': top_teams[1]['team'],
            'team2': top_teams[2]['team'],
            'played': False,
            'score1': 0,
            'score2': 0
        }
    ]
    
    # Final and third place matches will be created after semifinals are played
    return semifinals

def save_finals_schedule(finals_schedule):
    """Save the finals schedule to a separate file."""
    import json
    with open('finals_schedule.json', 'w') as f:
        json.dump(finals_schedule, f)

def load_finals_schedule():
    """Load the finals schedule from file."""
    import json
    try:
        with open('finals_schedule.json', 'r') as f:
            return json.load(f)
    except:
        return None
