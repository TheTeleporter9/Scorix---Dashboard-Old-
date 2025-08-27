"""Tournament logic with type hints."""

from typing import Dict, List, Tuple, Optional, Union, Any, TypedDict
from collections import defaultdict
from datetime import datetime

# Type definitions
class TeamData(TypedDict, total=False):
    Name: str
    Score: int
    Orange: int
    Purple: int

class GameData(TypedDict, total=False):
    GameNumber: Union[str, int]
    Team1: TeamData
    Team2: TeamData
    timestamp: str

def calculate_team_scores(games: List[GameData]) -> Dict[str, Dict[str, int]]:
    """Calculate scores for each team from all games."""
    scores = defaultdict(lambda: {'total': 0, 'orange': 0, 'purple': 0})
    
    for game in games:
        t1 = game.get('Team1', {})
        t2 = game.get('Team2', {})
        
        # Team 1 scores
        if 'Name' in t1 and 'Score' in t1:
            name = t1['Name']
            scores[name]['total'] += t1.get('Score', 0)
            scores[name]['orange'] += t1.get('Orange', 0)
            scores[name]['purple'] += t1.get('Purple', 0)
            
        # Team 2 scores
        if 'Name' in t2 and 'Score' in t2:
            name = t2['Name']
            scores[name]['total'] += t2.get('Score', 0)
            scores[name]['orange'] += t2.get('Orange', 0)
            scores[name]['purple'] += t2.get('Purple', 0)
            
    return dict(scores)

def get_sorted_team_scores(games: List[GameData]) -> List[Tuple[str, int]]:
    """Get a sorted list of (team_name, total_score) tuples."""
    scores = calculate_team_scores(games)
    return sorted(
        [(team, data['total']) for team, data in scores.items()],
        key=lambda x: x[1],
        reverse=True
    )

def calculate_total_scores(schedule: Dict[str, Any]) -> Dict[str, int]:
    """Calculate total scores for each team from the schedule."""
    matches = schedule.get('matches', [])
    teams = schedule.get('teams', [])
    scores = {team: 0 for team in teams}
    
    for match in matches:
        if not match.get('played', False):
            continue
            
        team1 = match.get('team1', '')
        team2 = match.get('team2', '')
        
        if team1 in scores:
            scores[team1] += match.get('score1', 0)
        if team2 in scores:
            scores[team2] += match.get('score2', 0)
            
    return scores

def get_all_teams(schedule: Dict[str, Any], games: List[GameData]) -> List[str]:
    """Get a list of all teams from both schedule and games."""
    teams = set(schedule.get('teams', []))
    
    for game in games:
        t1 = game.get('Team1', {}).get('Name')
        t2 = game.get('Team2', {}).get('Name')
        if t1:
            teams.add(t1)
        if t2:
            teams.add(t2)
            
    return sorted(list(teams))

class MatchComment(TypedDict):
    comment: str
    timestamp: str

class Match(TypedDict, total=False):
    team1: str
    team2: str
    played: bool
    penalty_team1: bool
    penalty_team2: bool
    comments: str
    comment_history: List[MatchComment]

Schedule = Dict[str, Union[List[str], List[Match]]]

def get_next_game(games: List[Dict[str, Any]]) -> int:
    """Get the next game number based on highest played game."""
    played_numbers = []
    for g in games:
        try:
            if 'GameNumber' in g:
                num = int(g['GameNumber'])
                played_numbers.append(num)
        except (TypeError, ValueError):
            continue
    return max(played_numbers, default=0) + 1

def get_leaderboard(games: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
    """Get sorted list of (team_name, avg_score) tuples."""
    scores = defaultdict(int)
    played = defaultdict(int)
    
    for g in games:
        t1 = g.get('Team1', {})
        t2 = g.get('Team2', {})
        for team in [t1, t2]:
            name = team.get('Name', '')
            score = team.get('Score', 0)
            if name and isinstance(score, (int, float)):
                scores[name] += score
                played[name] += 1
    
    # Calculate averages
    avg_scores = [
        (team, scores[team] / count)
        for team, count in played.items()
        if count > 0
    ]
    
    return sorted(avg_scores, key=lambda x: x[1], reverse=True)

def refresh_tournament_data() -> Dict[str, List[Dict[str, Any]]]:
    """Get fresh data from MongoDB."""
    data = list(collection.find())
    return {'games': data} if data else {'games': []}

def set_match_penalty_for_team(idx: int, team_num: int, penalty_value: bool, schedule: Schedule) -> None:
    """Set penalty for one team in a match."""
    matches = schedule.get('matches', [])
    if not isinstance(matches, list) or not 0 <= idx < len(matches):
        return
        
    match = matches[idx]
    if isinstance(match, dict):
        if team_num == 1:
            match['penalty_team1'] = penalty_value
        elif team_num == 2:
            match['penalty_team2'] = penalty_value

def get_team_scores_for_finals(games: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
    """Get team scores for finals qualification."""
    scores = defaultdict(lambda: {'total': 0, 'games': 0})
    
    for g in games:
        t1 = g.get('Team1', {})
        t2 = g.get('Team2', {})
        for team in [t1, t2]:
            name = team.get('Name', '')
            score = team.get('Score', 0)
            if name and isinstance(score, (int, float)):
                scores[name]['total'] += score
                scores[name]['games'] += 1
    
    # Calculate averages
    avg_scores = [
        (team, data['total'] / data['games'])
        for team, data in scores.items()
        if data['games'] > 0
    ]
    
    return sorted(avg_scores, key=lambda x: x[1], reverse=True)

def create_finals_schedule(top_teams: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
    """Create finals matches structure."""
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
