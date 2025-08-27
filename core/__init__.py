"""
Core functionality module.
"""

# Import new typed versions
from .match_scheduler_typed import (
    load_schedule, save_schedule, add_team, remove_team,
    generate_round_robin, set_match_comment_data,
    get_match_comment_data, get_match_data, set_match_played,
    add_comment_to_history
)
from .tournament_logic_typed import (
    calculate_team_scores, get_sorted_team_scores,
    calculate_total_scores, get_all_teams
)

# Import old modules for backward compatibility
from .display_publisher import *
from .finals import *
from .team_notes import *

__all__ = [
    'load_schedule', 'save_schedule', 'add_team', 'remove_team',
    'generate_round_robin', 'set_match_comment_data', 'get_match_comment_data',
    'get_match_data', 'set_match_played', 'add_comment_to_history',
    'calculate_team_scores', 'get_sorted_team_scores',
    'calculate_total_scores', 'get_all_teams'
]
