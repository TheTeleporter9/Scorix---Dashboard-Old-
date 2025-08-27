"""Tournament logic functions for managing games and teams."""
from typing import Dict, List, Tuple, Optional, Union, Any
from collections import defaultdict
from datetime import datetime

from data.mongodb_client import collection

# Type aliases
Schedule = Dict[str, Union[List[str], List[Dict[str, Any]]]]
Match = Dict[str, Any]
GameData = Dict[str, Union[str, Dict[str, Union[str, int]], datetime]]

GameData = Dict[str, Union[str, Dict[str, Union[str, int]], datetime]]

def get_next_game(games: List[GameData]) -> int:
    """Determines the next game number based on the highest played game."""
    played_numbers = []
    for g in games:
        try:
            num = int(g.get('GameNumber'))
            played_numbers.append(num)
        except (TypeError, ValueError):
            continue
    if not played_numbers:
        return 1
    return max(played_numbers) + 1

def get_leaderboard(games: List[GameData]) -> List[Tuple[str, float]]:
    """Returns a sorted list of (team_name, average_score) tuples."""
    scores = defaultdict(int)
    played = defaultdict(int)
    
    for g in games:
        t1, t2 = g.get('Team1', {}), g.get('Team2', {})
        for team in [t1, t2]:
            if 'Name' in team and 'Score' in team:
                scores[team['Name']] += team['Score']
                played[team['Name']] += 1
    
    # Calculate average scores
    avg_scores = []
    for team, score in scores.items():
        games = played[team]
        if games:  # Only include teams that played
            avg = score / games
            avg_scores.append((team, avg))
    
    return sorted(avg_scores, key=lambda x: x[1], reverse=True)

def refresh_tournament_data() -> Dict[str, List[GameData]]:
    """Gets fresh tournament data from the database."""
    games = list(collection.find())
    return {'games': games} if games else {'games': []}

def set_match_penalty_for_team(idx: int, team_num: int, penalty_value: bool, schedule: Schedule) -> None:
    """Set penalty for a specific team in a match.
    team_num should be 1 or 2."""
    if 0 <= idx < len(schedule['matches']):
        match = schedule['matches'][idx]
        if team_num == 1:
            match['penalty_team1'] = penalty_value
        elif team_num == 2:
            match['penalty_team2'] = penalty_value

def get_team_scores_for_finals(games: List[GameData]) -> List[Tuple[str, float]]:
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

def create_finals_schedule(top_teams: List[Tuple[str, float]]) -> List[Match]:
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
