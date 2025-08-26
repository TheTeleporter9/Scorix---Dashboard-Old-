from collections import defaultdict

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