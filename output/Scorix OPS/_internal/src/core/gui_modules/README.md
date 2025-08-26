# GUI Modules

This directory contains the modular functionality extracted from the main GUI file (`gui.py`). All GUI elements remain in the main file, but the business logic has been separated into logical modules for better maintainability and code organization.

## Module Structure

### `settings_manager.py`
Handles all settings-related operations:
- Loading and saving application settings
- Loading and saving competition display settings
- Default settings management

**Functions:**
- `load_settings()` - Load settings from file or return defaults
- `save_settings(settings)` - Save settings to file
- `load_comp_display_settings()` - Load competition display settings
- `save_comp_display_settings(settings)` - Save competition display settings

### `data_manager.py`
Handles data refresh and export operations:
- Refreshing data from MongoDB
- Exporting data to Excel
- Exporting schedule to CSV

**Functions:**
- `refresh_data()` - Refresh all data from MongoDB and return updated data
- `export_excel()` - Export games data to Excel
- `export_schedule_csv(schedule)` - Export schedule to CSV format

### `team_manager.py`
Handles team-related operations:
- Adding and removing teams from schedule
- Setting number of matches per team
- Auto-generating round robin schedules
- Managing team notes

**Functions:**
- `add_team_to_schedule(team_name, randomize, schedule)` - Add a team to the schedule
- `remove_team_from_schedule(team_name, randomize, schedule)` - Remove selected team from schedule
- `set_matches_per_team(num_matches, randomize, schedule)` - Set number of matches per team
- `auto_generate_schedule(randomize, schedule)` - Auto-generate round robin schedule
- `get_teams_list(schedule)` - Get list of teams from schedule
- `save_team_notes(team_notes)` - Save team notes to file
- `load_team_notes()` - Load team notes from file

### `match_manager.py`
Handles match-related operations:
- Getting and setting match data
- Managing match status, penalties, referees, and scores
- Setting next up matches
- Loading and saving schedules

**Functions:**
- `get_match_data(match_id)` - Get match data by ID
- `set_match_status(match_id, status)` - Set match status
- `set_match_penalty_for_team(match_id, team, penalty)` - Set penalty for a team in a match
- `set_match_referee(match_id, referee)` - Set referee for a match
- `set_match_scores(match_id, score1, score2)` - Set scores for a match
- `set_next_up_match(match_id)` - Set a match as next up
- `get_matches_list(schedule)` - Get list of matches from schedule
- `save_schedule_to_file(schedule, show_popup=True)` - Save schedule to file
- `load_schedule_from_file()` - Load schedule from file
- `get_next_up_match_from_schedule(schedule)` - Get the next up match from schedule

**Constants:**
- `MATCH_STATUSES` - Available match statuses
- `REFEREES` - Available referee options

### `comment_manager.py`
Handles comment-related operations:
- Setting and getting match comments
- Managing comment history
- Adding comments to team history

**Functions:**
- `set_match_comment_data(match_id, comment)` - Set comment for a match
- `get_match_comment_data(match_id)` - Get comment for a match
- `add_comment_to_history(match_id, old_comment, timestamp)` - Add comment to match history
- `get_comment_history()` - Get all comment history from MongoDB
- `get_team_comment_history(team)` - Get comment history for a specific team
- `clear_comment_history()` - Clear all comment history
- `delete_comment_from_history(comment_id)` - Delete a specific comment from history

### `finals_manager.py`
Handles finals bracket logic:
- Getting top teams for finals
- Creating finals schedules
- Managing finals match winners
- Saving and loading finals schedules

**Functions:**
- `get_top_teams_for_finals(num_teams=4)` - Get top teams for finals bracket
- `create_finals_schedule(top_teams)` - Create finals bracket schedule
- `set_finals_match_winner(match_type, match_index, winner, finals_schedule)` - Set winner for a finals match
- `save_finals_schedule(finals_schedule)` - Save finals schedule to file
- `load_finals_schedule()` - Load finals schedule from file

## Usage

The main GUI file (`gui.py`) imports all necessary functions from these modules and uses them to handle the business logic while keeping all GUI elements in the main file. This separation allows for:

1. **Better maintainability** - Business logic is separated from UI code
2. **Easier testing** - Functions can be tested independently
3. **Code reusability** - Functions can be used by other parts of the application
4. **Clearer organization** - Related functionality is grouped together

## Dependencies

These modules depend on:
- `mongodb_client` - For database operations
- `tournament_logic` - For tournament-specific logic
- `excel_exporter` - For Excel export functionality
- `match_scheduler` - For schedule management
- `pymongo` - For MongoDB operations
- `datetime` - For timestamp handling
- `json` - For file I/O operations
- `os` - For file system operations 