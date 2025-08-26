# GUI Modules Package
# This package contains all the functionality extracted from the main GUI file
#CJM

from .settings_manager import (
    load_settings, save_settings, 
    load_comp_display_settings, save_comp_display_settings
)

from .data_manager import (
    refresh_tournament_data, export_excel, export_schedule_csv
)

from .team_manager import (
    add_team_to_schedule, remove_team_from_schedule, 
    set_matches_per_team, auto_generate_schedule,
    get_teams_list, save_team_notes, load_team_notes
)

from .match_manager import (
    get_match_data, set_match_status, set_match_penalty_for_team,
    set_match_referee, set_match_scores, set_next_up_match,
    get_matches_list, save_schedule_to_file, load_schedule_from_file,
    get_next_up_match_from_schedule, MATCH_STATUSES, REFEREES,
    get_match_comment_data
)

from .comment_manager import (
    set_match_comment_data,
    add_comment_to_history, get_comment_history,
    get_team_comment_history, clear_comment_history,
    delete_comment_from_history
)

from .finals_manager import (
    get_top_teams_for_finals, create_finals_schedule,
    set_finals_match_winner, save_finals_schedule, load_finals_schedule
)

from .data_sync_manager import (
    sync_scores_from_mongodb, update_mongodb_from_schedule,
    get_all_teams_from_schedule_and_games, get_team_scores_for_finals
)

__all__ = [
    # Settings
    'load_settings', 'save_settings', 'load_comp_display_settings', 'save_comp_display_settings',
    
    # Data
    'refresh_tournament_data', 'export_excel', 'export_schedule_csv',
    
    # Teams
    'add_team_to_schedule', 'remove_team_from_schedule', 'set_matches_per_team', 
    'auto_generate_schedule', 'get_teams_list', 'save_team_notes', 'load_team_notes',
    
    # Matches
    'get_match_data', 'set_match_status', 'set_match_penalty_for_team', 'set_match_referee',
    'set_match_scores', 'set_next_up_match', 'get_matches_list', 'save_schedule_to_file',
    'load_schedule_from_file', 'get_next_up_match_from_schedule', 'MATCH_STATUSES', 'REFEREES',
    'set_match_comment_data',
    
    # Comments
    'add_comment_to_history', 'get_comment_history', 'get_team_comment_history',
    'clear_comment_history', 'delete_comment_from_history',
    
    # Finals
    'get_top_teams_for_finals', 'create_finals_schedule', 'set_finals_match_winner',
    'save_finals_schedule', 'load_finals_schedule',
    
    # Data Sync
    'sync_scores_from_mongodb', 'update_mongodb_from_schedule',
    'get_all_teams_from_schedule_and_games', 'get_team_scores_for_finals'
] 