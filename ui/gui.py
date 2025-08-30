"""
Tournament GUI application main file.
"""

from typing import Dict, List, Any, Optional, Union, TypedDict, cast
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
from datetime import datetime

from core import (
    load_schedule, save_schedule,
    set_match_played, add_team, remove_team,
    generate_round_robin, calculate_team_scores,
    get_sorted_team_scores, calculate_total_scores,
    get_all_teams
)
from core.match_scheduler import (
    get_match_data, get_match_comment_data,
    Schedule, Match, MatchComment
)
from core.tournament_logic import get_leaderboard, get_next_game
from ui.components.app_state import Settings

# Game types
class TeamData(TypedDict, total=False):
    Name: str
    Score: int
    Orange: int
    Purple: int
    penalty: bool

class GameData(TypedDict, total=False):
    GameNumber: Union[str, int]
    Team1: TeamData
    Team2: TeamData
    timestamp: str
    Team1: TeamData
    Team2: TeamData
    timestamp: str

def add_team_to_schedule(team_name: str, randomize: bool, schedule: Schedule) -> Schedule:
    """Add a team to the schedule"""
    add_team(schedule, team_name, randomize)
    return schedule

def remove_team_from_schedule(team_name: str, randomize: bool, schedule: Schedule) -> Schedule:
    """Remove a team from the schedule"""
    remove_team(schedule, team_name, randomize)
    return schedule

def set_matches_per_team(n: int, randomize: bool, schedule: Schedule) -> Schedule:
    """Set the number of matches per team"""
    schedule['matches'] = generate_round_robin(schedule['teams'], n, randomize)
    save_schedule(schedule)
    return schedule

def auto_generate_schedule(randomize: bool, schedule: Schedule) -> Schedule:
    """Auto generate schedule for all teams"""
    if schedule['teams']:
        schedule['matches'] = generate_round_robin(schedule['teams'], 1, randomize)
        save_schedule(schedule)
    return schedule

def set_match_penalty_for_team(idx: int, team_num: int, penalty: bool, schedule: Schedule) -> None:
    """Set penalty for a team in a match"""
    if 0 <= idx < len(schedule['matches']):
        key = f'penalty_team{team_num}'
        schedule['matches'][idx][key] = penalty
        save_schedule(schedule)

from data.mongodb_client import collection, live_announce_collection
from utils.excel_exporter import export_excel, export_schedule_csv
from core.display_publisher import publish_to_display
from core.team_notes import save_team_notes, load_team_notes
from ui.components.app_state import AppState, load_settings, save_settings
from core.match_scheduler import (
    MATCH_STATUSES,
    set_match_comment_data,
    get_match_comment_data,
    add_comment_to_history
)
from ui.components.scores_tab import ScoresTab
from ui.components.operator_tab import OperatorTab
from ui.components.games_tab import GamesTab
from ui.components.settings_tab import SettingsTab
from ui.components.comment_history_tab import CommentHistoryTab
from ui.components.finals_bracket import FinalsBracket # type: ignore

# Import the new modular functionality
from tkinter import filedialog
from typing import cast
from ui.components import (
    AppState, GamesTab, ScoresTab, SettingsTab, 
    OperatorTab, CommentHistoryTab, FinalsBracket
)
from ui.components.app_state import (
    load_settings, save_settings, load_comp_display_settings, save_comp_display_settings,
    update_mongodb_from_schedule, sync_scores_from_mongodb, get_all_teams_from_schedule_and_games
)
from utils.excel_exporter import export_games_to_excel
from data.db_utils import publish_display_data
from utils.type_utils import ensure_dict

print('Starting Tournament GUI...')

# CJM
class TournamentApp(tk.Tk):
    def __init__(self):
        print('Initializing TournamentApp...')
        super().__init__()
        self.title('SCORIX')
        
        # Initialize tree widgets
        from typing import Optional
        from tkinter import ttk
        self.scheduled_tree: Optional[ttk.Treeview] = None
        self.completed_tree: Optional[ttk.Treeview] = None
        self.standings_tree: Optional[ttk.Treeview] = None
        
        # Helper method for type safety
        def ensure_tree(tree: Optional[ttk.Treeview], name: str) -> ttk.Treeview:
            if tree is None:
                raise RuntimeError(f"{name} tree not initialized")
            return tree
            
        self._ensure_scheduled_tree = lambda: ensure_tree(self.scheduled_tree, "scheduled matches")
        self._ensure_completed_tree = lambda: ensure_tree(self.completed_tree, "completed matches")
        self._ensure_standings_tree = lambda: ensure_tree(self.standings_tree, "standings")
        
        # Initialize application state
        self.app_state = AppState()
        settings_dict = cast(Dict[str, Any], load_settings())
        self.app_state.settings = settings_dict
        schedule_dict = cast(Dict[str, Any], load_schedule())
        self.app_state.schedule = schedule_dict
        self.app_state.root = self
        
        # Keep references for easier access
        self.settings: Settings = self.app_state.settings
        self.schedule: Schedule = self.app_state.schedule
        
        # Load logo image
        try:
            logo_img = Image.open('scorix_logo.png').resize((120, 120))
            self.logo_img = ImageTk.PhotoImage(logo_img)
            self.iconphoto(True, self.logo_img)
        except Exception as e:
            print('Logo image not found or failed to load:', e)
            self.logo_img = None

        self.apply_theme()
        self.create_logo_top_right()
        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Start periodic display data publishing
        self.app_state.display_update_interval = 30 * 1000  # 30 seconds
        self.app_state.display_update_job = None
        self.schedule_display_update()
        
    def update_display(self):
        """Update the tournament display data"""
        # Update MongoDB collection
        finals_data = getattr(self.app_state, 'finals_data', None)
        publish_to_display(self.schedule, finals_data)
        
        # Update tournament data display
        from data.mongodb_client import collection
        try:
            data = list(collection.find())
            if data:
                self.app_state.tournament_data = data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")
        
        try:
            # Update trees if they exist
            if hasattr(self, 'scheduled_tree'):
                self.update_scheduled_matches_tree()
            if hasattr(self, 'completed_tree'):
                self.update_completed_matches_tree()
            if hasattr(self, 'standings_tree'):
                self.update_team_standings()
                
            # Save current state
            save_schedule(self.schedule)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to update display: {e}')
        
    def _ensure_tree(self, tree: Optional[ttk.Treeview], name: str) -> ttk.Treeview:
        """Ensure a treeview is initialized."""
        if tree is None:
            raise RuntimeError(f"{name} treeview not initialized")
        return tree

    def update_scheduled_matches_tree(self) -> None:
        """Update the scheduled matches treeview"""
        tree = self._ensure_tree(self.scheduled_tree, "scheduled matches")
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Add matches to tree
        for i, m in enumerate(self.schedule['matches']):
            if not m['played']:
                team1, team2 = m['team1'], m['team2']
                played = 'Yes' if m['played'] else 'No'
                penalty1 = '*' if m['penalty_team1'] else ''
                penalty2 = '*' if m['penalty_team2'] else ''
                comments = m.get('comments', '')
                tree.insert('', 'end', values=(i, team1, team2, played, penalty1, penalty2, comments))
                
    def update_completed_matches_tree(self) -> None:
        """Update the completed matches treeview"""
        tree = self._ensure_tree(self.completed_tree, "completed matches")
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        for i, m in enumerate(self.schedule['matches']):
            if m['played']:
                team1, team2 = m['team1'], m['team2']
                played = 'Yes' if m['played'] else 'No'
                penalty1 = '*' if m['penalty_team1'] else ''
                penalty2 = '*' if m['penalty_team2'] else ''
                comments = m.get('comments', '')
                self.completed_tree.insert('', 'end', values=(i, team1, team2, played, penalty1, penalty2, comments))
                
    def update_team_standings(self) -> None:
        """Update the team standings display"""
        tree = self._ensure_standings_tree()
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Get leaderboard data
        leaderboard = get_leaderboard(self.app_state.tournament_data)
        
        # Add teams to tree
        for i, (team, score) in enumerate(leaderboard, 1):
            rank = str(i)
            tree.insert('', 'end', values=(rank, team, score))

    def create_logo_top_right(self):
        if not self.logo_img:
            return
        # Place larger logo at the top right, above the notebook
        self.logo_tr = tk.Label(self, image=self.logo_img, bg=self['bg'])
        self.logo_tr.place(relx=1.0, y=0, anchor='ne')
        
    def _configure_tree(self, tree, columns, widths=None):
        """Configure column headings and widths for a treeview"""
        # Default widths if none provided
        if widths is None:
            widths = {
                'match': 50, 'team1': 100, 'team2': 100,
                'played': 50, 'penalty1': 30, 'penalty2': 30,
                'comments': 150, 'rank': 50, 'team': 100,
                'score': 70
            }
        
        # Set column headings
        headings = {
            'match': 'Match', 'team1': 'Team 1', 'team2': 'Team 2',
            'played': 'Played', 'penalty1': 'P1', 'penalty2': 'P2',
            'comments': 'Comments', 'rank': 'Rank', 'team': 'Team',
            'score': 'Score'
        }
        
        for col in columns:
            if col in headings:
                tree.heading(col, text=headings[col])
            if col in widths:
                tree.column(col, width=widths[col])
                
        return tree
        
    def _create_scrolled_treeview(self, parent, columns):
        """Create a treeview with scrollbar in a frame"""
        frame = ttk.Frame(parent)
        
        # Create tree
        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        scrollbar.config(command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack components
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        frame.pack(fill=tk.BOTH, expand=True)
        
        return frame, tree
        
    def create_scheduled_matches_frame(self, parent):
        """Create the scheduled matches frame with tree and scrollbar"""
        columns = ('match', 'team1', 'team2', 'played', 'penalty1', 'penalty2', 'comments')
        frame, tree = self._create_scrolled_treeview(parent, columns)
        
        # Configure tree
        self.scheduled_tree = tree = self._configure_tree(tree, columns)
        
        # Bind events
        tree.bind('<Double-1>', self.toggle_match_played)
        tree.bind('<Return>', self.toggle_match_played)
        
        return frame
        
    def create_completed_matches_frame(self, parent: ttk.Frame) -> ttk.Frame:
        """Create the completed matches frame with tree and scrollbar"""
        columns = ['match', 'team1', 'team2', 'played', 'penalty1', 'penalty2', 'comments']
        headings = {
            'match': 'Match',
            'team1': 'Team 1',
            'team2': 'Team 2',
            'played': 'Played',
            'penalty1': 'P1',
            'penalty2': 'P2',
            'comments': 'Comments'
        }
        widths = {
            'match': 50,
            'team1': 100,
            'team2': 100,
            'played': 50,
            'penalty1': 30,
            'penalty2': 30,
            'comments': 150
        }
        
        from ui.components.tree_widget import create_scrolled_treeview
        frame, tree = create_scrolled_treeview(parent, columns, headings, widths)
        self.completed_tree = tree
        
        return frame
    
    def create_team_standings_frame(self, parent: ttk.Frame) -> ttk.Frame:
        """Create the team standings frame with tree and scrollbar"""
        columns = ['rank', 'team', 'score']
        headings = {
            'rank': 'Rank',
            'team': 'Team',
            'score': 'Score'
        }
        widths = {
            'rank': 50,
            'team': 100,
            'score': 70
        }
        
        from ui.components.tree_widget import create_scrolled_treeview
        frame, tree = create_scrolled_treeview(parent, columns, headings, widths)
        self.standings_tree = tree
        
        return frame
        
        # Set column headings
        self.completed_tree.heading('match', text='Match')
        self.completed_tree.heading('team1', text='Team 1')
        self.completed_tree.heading('team2', text='Team 2')
        self.completed_tree.heading('played', text='Played')
        self.completed_tree.heading('penalty1', text='P1')
        self.completed_tree.heading('penalty2', text='P2')
        self.completed_tree.heading('comments', text='Comments')
        
        # Set column widths
        self.completed_tree.column('match', width=50)
        self.completed_tree.column('team1', width=100)
        self.completed_tree.column('team2', width=100)
        self.completed_tree.column('played', width=50)
        self.completed_tree.column('penalty1', width=30)
        self.completed_tree.column('penalty2', width=30)
        self.completed_tree.column('comments', width=150)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.completed_tree.yview)
        self.completed_tree.configure(yscroll=scrollbar.set)
        
        # Pack components
        self.completed_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        frame.pack(fill=tk.BOTH, expand=True)
        return frame
        
    def create_team_standings_frame(self, parent):
        """Create the team standings frame with tree and scrollbar"""
        frame = ttk.Frame(parent)
        
        # Create tree
        columns = ('rank', 'team', 'score')
        self.standings_tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        
        # Set column headings
        self.standings_tree.heading('rank', text='Rank')
        self.standings_tree.heading('team', text='Team')
        self.standings_tree.heading('score', text='Score')
        
        # Set column widths
        self.standings_tree.column('rank', width=50)
        self.standings_tree.column('team', width=100)
        self.standings_tree.column('score', width=70)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.standings_tree.yview)
        self.standings_tree.configure(yscroll=scrollbar.set)
        
        # Pack components
        self.standings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        frame.pack(fill=tk.BOTH, expand=True)
        return frame
        
    def toggle_match_played(self, event=None) -> None:
        """Toggle the played status of a match when double-clicked"""
        tree = self._ensure_scheduled_tree()
            
        sel = tree.selection()
        if not sel:
            return
            
        try:
            idx = int(tree.item(sel[0])['values'][0])
            m = get_match_data(idx, self.schedule)
            if m:
                played = not m.get('played', False)
                set_match_played(self.schedule, idx, played)
                self.update_display()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to toggle match status: {e}')
        
        # Set column headings
        self.scheduled_tree.heading('match', text='Match')
        self.scheduled_tree.heading('team1', text='Team 1')
        self.scheduled_tree.heading('team2', text='Team 2')
        self.scheduled_tree.heading('played', text='Played')
        self.scheduled_tree.heading('penalty1', text='P1')
        self.scheduled_tree.heading('penalty2', text='P2')
        self.scheduled_tree.heading('comments', text='Comments')
        
        # Set column widths
        self.scheduled_tree.column('match', width=50)
        self.scheduled_tree.column('team1', width=100)
        self.scheduled_tree.column('team2', width=100)
        self.scheduled_tree.column('played', width=50)
        self.scheduled_tree.column('penalty1', width=30)
        self.scheduled_tree.column('penalty2', width=30)
        self.scheduled_tree.column('comments', width=150)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.scheduled_tree.yview)
        self.scheduled_tree.configure(yscroll=scrollbar.set)
        
        # Pack components
        self.scheduled_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.scheduled_tree.bind('<Double-1>', self.toggle_match_played)
        self.scheduled_tree.bind('<Return>', self.toggle_match_played)
        
        return self.scheduled_tree

    def apply_theme(self):
        if not hasattr(self, 'app_state'):
            self.app_state = AppState()
            self.app_state.settings = load_settings()
        
        if self.app_state.settings.get('dark_mode', False):
            color = '#23272e'
            fg = '#f0f0f0'
        else:
            color = self.app_state.settings.get('theme_color', '#e3f2fd')
            fg = '#000000'
        self.configure(bg=self.app_state.get_setting('theme_color', '#e3f2fd'))
        # Update all frames if they exist
        for frame in getattr(self, 'notebook', []), getattr(self, 'scores_frame', None), getattr(self, 'operator_frame', None), getattr(self, 'games_frame', None), getattr(self, 'settings_frame', None):
            if isinstance(frame, tk.Frame):
                frame.configure(bg=self.app_state.get_setting('theme_color', '#e3f2fd'))
        # Update all labels and buttons
        def update_widget_colors(widget):
            if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton, tk.Entry, tk.Listbox, tk.LabelFrame, tk.Frame)):
                try:
                    if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton)):
                        widget.configure(bg=self.app_state.get_setting('theme_color', '#e3f2fd'), fg=fg)
                    else:
                        widget.configure(bg=self.app_state.get_setting('theme_color', '#e3f2fd'))
                except:
                    pass
            for child in getattr(widget, 'winfo_children', lambda: [])():
                update_widget_colors(child)
        if hasattr(self, 'notebook'):
            for tab in self.notebook.winfo_children():
                update_widget_colors(tab)

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        
        # Scores tab
        bg_color = self.app_state.get_setting('theme_color', '#e3f2fd')
        
        self.scores_frame = tk.Frame(self.notebook, bg=bg_color)
        self.notebook.add(self.scores_frame, text='🏆 Scores')
        self.scores_tab = ScoresTab(self.scores_frame, self.app_state)
        
        # Operator tab
        self.operator_frame = tk.Frame(self.notebook, bg=bg_color)
        self.notebook.add(self.operator_frame, text='🛠️ Operator')
        self.operator_tab = OperatorTab(self.operator_frame, self.app_state)
        
        # Games tab
        self.games_frame = tk.Frame(self.notebook, bg=bg_color)
        self.notebook.add(self.games_frame, text='🎮 Games')
        self.games_tab = GamesTab(self.games_frame, self.app_state)
        
        # Comment History tab
        self.comment_history_frame = tk.Frame(self.notebook, bg=bg_color)
        self.notebook.add(self.comment_history_frame, text='📝 Comment History')
        self.comment_history_tab = CommentHistoryTab(self.comment_history_frame, self.app_state)
        
        # Settings tab
        self.settings_frame = tk.Frame(self.notebook, bg=bg_color)
        self.notebook.add(self.settings_frame, text='⚙️ Settings')
        self.settings_tab = SettingsTab(self.settings_frame, self.app_state)
        
        # Bind tab change events
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        self._last_tab = None

    def create_scores_tab(self, parent):
        # CJM label in corner
        cjm_label = tk.Label(parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        # Next game label
        self.next_game_label = tk.Label(parent, text='', font=('Arial', 16, 'bold'), bg=self.settings['theme_color'])
        self.next_game_label.pack(pady=10)

        # Games frame
        games_frame = tk.LabelFrame(parent, text='Games Played', font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
        games_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.games_tree = ttk.Treeview(games_frame, columns=(
            'Game', 'Timestamp', 'Team', 'Score', 'O Balls', 'P Balls', 'Last Updated'), show='headings', height=10)
        for col in self.games_tree['columns']:
            self.games_tree.heading(col, text=col)
            if col == 'Last Updated':
                self.games_tree.column(col, anchor='center', width=150)
            else:
                self.games_tree.column(col, anchor='center', width=120)
        self.games_tree.pack(fill='both', expand=True)

        # Leaderboard frame
        leaderboard_frame = tk.LabelFrame(parent, text='Leaderboard', font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
        leaderboard_frame.pack(fill='x', padx=10, pady=5)
        self.leaderboard_tree = ttk.Treeview(leaderboard_frame, columns=('Team', 'Score', 'Last Updated'), show='headings', height=5)
        self.leaderboard_tree.heading('Team', text='Team')
        self.leaderboard_tree.heading('Score', text='Score')
        self.leaderboard_tree.heading('Last Updated', text='Last Updated')
        self.leaderboard_tree.column('Team', anchor='center', width=200)
        self.leaderboard_tree.column('Score', anchor='center', width=100)
        self.leaderboard_tree.column('Last Updated', anchor='center', width=150)
        self.leaderboard_tree.pack(fill='x')

        # Buttons
        btn_frame = tk.Frame(parent, bg=self.settings['theme_color'])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='Refresh', command=self.refresh_data, bg='#4CAF50', fg='white', font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        tk.Button(btn_frame, text='Export to Excel', command=self.export_excel, bg='#2196F3', fg='white', font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        tk.Button(btn_frame, text='Upload Display Now', command=self.upload_display_now, bg='#FF9800', fg='white', font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        
        # Auto-refresh setup
        self.auto_refresh_enabled = True
        self.auto_refresh_interval = 30  # seconds
        self.schedule_auto_refresh()

    def create_operator_tab(self, parent):
        bg_color = self.app_state.get_setting('theme_color', '#e3f2fd')
        randomize = self.app_state.get_setting('randomize_schedule', True)
        
        # CJM label in corner
        cjm_label = tk.Label(parent, text='CJM', font=('Arial', 8), bg=bg_color)
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        # Teams management
        teams_frame = tk.LabelFrame(parent, text='Teams', font=('Arial', 12, 'bold'), bg=bg_color)
        teams_frame.pack(fill='x', padx=10, pady=5)
        self.teams_listbox = tk.Listbox(teams_frame, height=6)
        self.teams_listbox.pack(side='left', padx=5, pady=5)
        self.refresh_teams_listbox()
        team_entry = tk.Entry(teams_frame)
        team_entry.pack(side='left', padx=5)
        tk.Button(teams_frame, text='Add Team', command=lambda: self.add_team(team_entry.get(), randomize)).pack(side='left', padx=5)
        tk.Button(teams_frame, text='Remove Team', command=lambda: self.remove_selected_team(randomize)).pack(side='left', padx=5)

        # Number of matches
        matches_frame = tk.Frame(parent, bg=bg_color)
        matches_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(matches_frame, text='Matches per team:', bg=bg_color).pack(side='left')
        self.num_matches_var = tk.IntVar(value=1)
        matches_entry = tk.Entry(matches_frame, textvariable=self.num_matches_var, width=5)
        matches_entry.pack(side='left', padx=5)
        tk.Button(matches_frame, text='Set', command=lambda: self.set_num_matches(self.settings['randomize_schedule'])).pack(side='left', padx=5)
        tk.Button(matches_frame, text='Auto-generate Schedule', command=lambda: self.auto_generate_schedule(self.settings['randomize_schedule'])).pack(side='left', padx=5)

        # Matches table (show played status)
        matches_table_frame = tk.LabelFrame(parent, text='Scheduled Matches', font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
        matches_table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.matches_tree = ttk.Treeview(matches_table_frame, columns=('Team 1', 'Team 2', 'Played'), show='headings', height=10)
        for col in self.matches_tree['columns']:
            self.matches_tree.heading(col, text=col)
            self.matches_tree.column(col, anchor='center', width=150)
        self.matches_tree.pack(fill='both', expand=True)
        self.refresh_matches_tree()

        # Save button
        tk.Button(parent, text='Save Schedule', command=self.save_schedule).pack(pady=10)
        # Finals button
        tk.Button(parent, text='Start Finals', command=self.start_finals).pack(pady=10)

        # Team notes
        notes_frame = tk.LabelFrame(parent, text='Team Notes', font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
        notes_frame.pack(fill='x', padx=10, pady=5)
        self.notes_text = tk.Text(notes_frame, height=4, width=60)
        self.notes_text.pack(side='left', padx=5)
        tk.Button(notes_frame, text='Save Notes', command=self.save_team_notes).pack(side='left', padx=5)
        self.refresh_team_notes()

    def create_comment_history_tab(self, parent):
        # CJM label in corner
        cjm_label = tk.Label(parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        tk.Label(parent, text='Comment History', font=('Arial', 16, 'bold'), bg=self.settings['theme_color']).pack(pady=10)
        self.comment_tree = ttk.Treeview(parent, columns=('Match', 'Team 1', 'Team 2', 'Old Comment', 'Timestamp'), show='headings', height=20)
        for col in self.comment_tree['columns']:
            self.comment_tree.heading(col, text=col)
            self.comment_tree.column(col, anchor='center', width=180)
        self.comment_tree.pack(fill='both', expand=True)
        self.refresh_comment_history()

    def create_settings_tab(self, parent):
        # CJM label in corner
        cjm_label = tk.Label(parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        tk.Label(parent, text='Settings', font=('Arial', 16, 'bold'), bg=self.settings['theme_color']).pack(pady=10)
        # Theme color
        tk.Label(parent, text='Theme Color:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        color_var = tk.StringVar(value=self.settings.get('theme_color', '#e3f2fd'))
        color_menu = ttk.Combobox(parent, textvariable=color_var, values=['#e3f2fd', '#fce4ec', '#fffde7', '#e8f5e9', '#ede7f6', '#fff3e0'], state='readonly')
        color_menu.pack(anchor='w', padx=40, pady=2)
        # Default matches per team
        tk.Label(parent, text='Default Matches per Team:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        matches_var = tk.IntVar(value=self.settings.get('default_matches_per_team', 1))
        matches_entry = tk.Entry(parent, textvariable=matches_var, width=5)
        matches_entry.pack(anchor='w', padx=40, pady=2)
        # Randomize schedule
        rand_var = tk.BooleanVar(value=self.settings.get('randomize_schedule', True))
        rand_check = tk.Checkbutton(parent, text='Randomize Schedule Order', variable=rand_var, bg=self.settings['theme_color'])
        rand_check.pack(anchor='w', padx=20, pady=2)
        # Enable Dark Mode
        tk.Label(parent, text='Enable Dark Mode:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        dark_var = tk.BooleanVar(value=self.settings.get('dark_mode', False))
        dark_check = tk.Checkbutton(parent, text='Enable Dark Mode', variable=dark_var, bg=self.settings['theme_color'])
        dark_check.pack(anchor='w', padx=40, pady=2)
        # Notification Sound
        tk.Label(parent, text='Notification Sound:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        notif_var = tk.BooleanVar(value=self.settings.get('notification_sound', True))
        notif_check = tk.Checkbutton(parent, text='Play sound on event', variable=notif_var, bg=self.settings['theme_color'])
        notif_check.pack(anchor='w', padx=40, pady=2)
        # Font size
        tk.Label(parent, text='Font Size:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        font_var = tk.IntVar(value=self.settings.get('font_size', 12))
        font_entry = tk.Entry(parent, textvariable=font_var, width=5)
        font_entry.pack(anchor='w', padx=40, pady=2)
        # Highlight color
        tk.Label(parent, text='Highlight Color:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        highlight_var = tk.StringVar(value=self.settings.get('highlight_color', '#90caf9'))
        highlight_entry = tk.Entry(parent, textvariable=highlight_var, width=10)
        highlight_entry.pack(anchor='w', padx=40, pady=2)
        # Https server IP
        tk.Label(parent, text='HTTPS Server IP:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        https_ip_var = tk.StringVar(value=self.settings.get('https_server_ip', ''))
        https_ip_entry = tk.Entry(parent, textvariable=https_ip_var, width=15)
        https_ip_entry.pack(anchor='w', padx=40, pady=2)
        # Autosave interval
        tk.Label(parent, text='Autosave Interval (seconds):', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        autosave_var = tk.IntVar(value=self.settings.get('autosave_interval', 30))
        autosave_entry = tk.Entry(parent, textvariable=autosave_var, width=5)
        autosave_entry.pack(anchor='w', padx=40, pady=2)
        # Display settings section
        display_var = tk.BooleanVar(value=False)
        def toggle_display():
            if display_var.get():
                display_frame.pack(fill='x', padx=20, pady=10)
            else:
                display_frame.pack_forget()
        display_check = tk.Checkbutton(parent, text='Show Display Settings', variable=display_var, command=toggle_display, bg=self.settings['theme_color'])
        display_check.pack(anchor='w', padx=20, pady=10)
        display_frame = tk.Frame(parent, bg=self.settings['theme_color'])
        comp_display_settings = load_comp_display_settings()
        disp_uri_var = tk.StringVar(value=comp_display_settings.get('DISPLAY_MONGO_URI', ''))
        disp_db_var = tk.StringVar(value=comp_display_settings.get('DISPLAY_DB_NAME', ''))
        disp_coll_var = tk.StringVar(value=comp_display_settings.get('DISPLAY_COLLECTION_NAME', ''))
        tk.Label(display_frame, text='Display MongoDB URI:', bg=self.settings['theme_color']).pack(anchor='w')
        tk.Entry(display_frame, textvariable=disp_uri_var, width=50).pack(anchor='w', pady=2)
        tk.Label(display_frame, text='Display Database Name:', bg=self.settings['theme_color']).pack(anchor='w')
        tk.Entry(display_frame, textvariable=disp_db_var, width=30).pack(anchor='w', pady=2)
        tk.Label(display_frame, text='Display Collection Name:', bg=self.settings['theme_color']).pack(anchor='w')
        tk.Entry(display_frame, textvariable=disp_coll_var, width=30).pack(anchor='w', pady=2)
        # Save button
        def save_and_apply():
            self.settings['theme_color'] = color_var.get()
            self.settings['default_matches_per_team'] = matches_var.get()
            self.settings['randomize_schedule'] = rand_var.get()
            self.settings['dark_mode'] = dark_var.get()
            self.settings['notification_sound'] = notif_var.get()
            self.settings['font_size'] = font_var.get()
            self.settings['highlight_color'] = highlight_var.get()
            self.settings['autosave_interval'] = autosave_var.get()
            self.settings['https_server_ip'] = https_ip_var.get()
            save_settings(self.settings)
            # Save display MongoDB settings if visible
            if display_var.get():
                save_comp_display_settings({
                    'DISPLAY_MONGO_URI': disp_uri_var.get(),
                    'DISPLAY_DB_NAME': disp_db_var.get(),
                    'DISPLAY_COLLECTION_NAME': disp_coll_var.get(),
                })
            self.apply_theme()
            for frame in [self.scores_frame, self.operator_frame, self.games_frame, self.settings_frame, self.comment_history_frame]:
                frame.configure(bg=self.settings['theme_color'] if not self.settings.get('dark_mode', False) else '#23272e')
            messagebox.showinfo('Settings', 'Settings saved and theme applied!')
        tk.Button(parent, text='💾 Save Settings', command=save_and_apply, bg='#90caf9', fg='black').pack(pady=10)

    def create_games_tab(self, parent):
        # CJM label in corner
        cjm_label = tk.Label(parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        # Safety check: if no schedule loaded, show warning and disable controls
        if not self.schedule or not self.schedule.get('matches'):
            warning = tk.Label(parent, text='No schedule loaded. Please load or create a schedule first.', fg='red', font=('Arial', 14), bg=self.settings['theme_color'])
            warning.pack(pady=20)
            load_btn = tk.Button(parent, text='Load Schedule', command=self.load_schedule_from_file)
            load_btn.pack(pady=10)
            self.scheduled_tree = None
            self.completed_tree = None
            return
        # Scheduled games (not played)
        scheduled_frame = tk.LabelFrame(parent, text='Scheduled Games', font=('Arial', 12, 'bold'), bg='#e0f7fa')
        scheduled_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.scheduled_tree = ttk.Treeview(scheduled_frame, columns=(
            'Index', 'Team 1', 'Penalty 1', 'Team 2', 'Penalty 2', 'Comments', 'Status', 'Referee', 'Score 1', 'Score 2', 'Next Up'), show='headings', height=10)
        for col in self.scheduled_tree['columns']:
            self.scheduled_tree.heading(col, text=col)
            self.scheduled_tree.column(col, anchor='center', width=100)
        self.scheduled_tree.pack(fill='both', expand=True)

        # Completed games (played)
        completed_frame = tk.LabelFrame(parent, text='Completed Games', font=('Arial', 12, 'bold'), bg='#ffe0b2')
        completed_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.completed_tree = ttk.Treeview(completed_frame, columns=(
            'Index', 'Team 1', 'Penalty 1', 'Team 2', 'Penalty 2', 'Comments', 'Status', 'Referee', 'Score 1', 'Score 2', 'Next Up'), show='headings', height=10)
        for col in self.completed_tree['columns']:
            self.completed_tree.heading(col, text=col)
            self.completed_tree.column(col, anchor='center', width=100)
        self.completed_tree.pack(fill='both', expand=True)

        self.refresh_games_trees()

        # Right-click context menus
        self.sched_menu = tk.Menu(self.scheduled_tree, tearoff=0)
        self.sched_menu.add_command(label='Edit Comments', command=self.edit_comment_scheduled)
        self.sched_menu.add_command(label='View Comments', command=self.view_comment_scheduled)
        self.sched_menu.add_command(label='Edit Status', command=self.edit_status_scheduled)
        self.sched_menu.add_command(label='Edit Referee', command=self.edit_referee_scheduled)
        self.sched_menu.add_command(label='Edit Scores', command=self.edit_scores_scheduled)
        self.sched_menu.add_command(label='Set as Next Up', command=self.set_next_up_scheduled)
        self.scheduled_tree.bind('<Button-3>', self.show_sched_menu)

        self.comp_menu = tk.Menu(self.completed_tree, tearoff=0)
        self.comp_menu.add_command(label='Edit Comments', command=self.edit_comment_completed)
        self.comp_menu.add_command(label='View Comments', command=self.view_comment_completed)
        self.comp_menu.add_command(label='Edit Status', command=self.edit_status_completed)
        self.comp_menu.add_command(label='Edit Referee', command=self.edit_referee_completed)
        self.comp_menu.add_command(label='Edit Scores', command=self.edit_scores_completed)
        self.comp_menu.add_command(label='Set as Next Up', command=self.set_next_up_completed)
        self.completed_tree.bind('<Button-3>', self.show_comp_menu)

        # Filter/search bar
        filter_frame = tk.Frame(parent, bg=self.settings['theme_color'])
        filter_frame.pack(fill='x', padx=10, pady=2)
        tk.Label(filter_frame, text='Filter by Team or Status:', bg=self.settings['theme_color']).pack(side='left')
        self.filter_var = tk.StringVar()
        filter_entry = tk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.pack(side='left', padx=5)
        tk.Button(filter_frame, text='Apply Filter', command=self.refresh_games_trees).pack(side='left', padx=5)
        tk.Button(filter_frame, text='Export to CSV', command=self.export_schedule_csv).pack(side='left', padx=5)

        # Controls for updating status/penalties (for scheduled games only)
        control_frame = tk.Frame(parent, bg=self.settings['theme_color'])
        control_frame.pack(pady=10)
        tk.Label(control_frame, text='Select a scheduled game and:', bg=self.settings['theme_color']).pack(side='left')
        tk.Button(control_frame, text='Toggle Played', command=self.toggle_played_scheduled).pack(side='left', padx=5)
        tk.Button(control_frame, text='Toggle Penalty Team 1', command=lambda: self.toggle_penalty_scheduled(1)).pack(side='left', padx=5)
        tk.Button(control_frame, text='Toggle Penalty Team 2', command=lambda: self.toggle_penalty_scheduled(2)).pack(side='left', padx=5)
        tk.Button(control_frame, text='Save Changes', command=self.save_games_schedule).pack(side='left', padx=5)
        tk.Button(control_frame, text='Load Schedule', command=self.load_schedule_from_file).pack(side='left', padx=5)

        # Bind tab change events for autosave and autoload
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        self._last_tab = None

    def on_tab_changed(self, event):
        tab = self.notebook.select()
        tab_text = self.notebook.tab(tab, 'text')
        
        # Update current tab's data
        if tab_text == '� Scores':
            self.scores_tab.refresh_data()
        elif tab_text == '🛠️ Operator':
            self.operator_tab.refresh_data()
        elif tab_text == '🎮 Games':
            self.games_tab.refresh_games_trees()
        elif tab_text == '📝 Comment History':
            self.comment_history_tab.refresh_comment_history()
        
        self._last_tab = tab_text

    def view_comment_scheduled(self):
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        comment = get_match_comment_data(idx, self.schedule)
        messagebox.showinfo('Comment', comment if comment else 'No comment.')

    def view_comment_completed(self):
        sel = self.completed_tree.selection()
        if not sel:
            return
        idx = int(self.completed_tree.item(sel[0])['values'][0])
        comment = get_match_comment_data(idx, self.schedule)
        messagebox.showinfo('Comment', comment if comment else 'No comment.')

    def refresh_teams_listbox(self):
        self.teams_listbox.delete(0, tk.END)
        for team in self.schedule['teams']:
            self.teams_listbox.insert(tk.END, team)
    
    def refresh_operator_data(self):
        """Refresh operator tab data without recreating widgets"""
        self.refresh_teams_listbox()
        self.refresh_matches_tree()

    def add_team(self, team_name, randomize):
        if not team_name.strip():
            return
        self.schedule = add_team_to_schedule(team_name.strip(), randomize, self.schedule)
        self.refresh_teams_listbox()
        self.refresh_matches_tree()

    def remove_selected_team(self, randomize):
        selection = self.teams_listbox.curselection()
        if not selection:
            return
        team = self.teams_listbox.get(selection[0])
        self.schedule = remove_team_from_schedule(team, randomize, self.schedule)
        self.refresh_teams_listbox()
        self.refresh_matches_tree()

    def set_num_matches(self, randomize):
        try:
            n = int(self.num_matches_var.get())
            self.schedule = set_matches_per_team(n, randomize, self.schedule)
            self.refresh_matches_tree()
        except ValueError:
            messagebox.showerror('Error', 'Invalid number of matches')

    def auto_generate_schedule(self, randomize):
        self.schedule = auto_generate_schedule(randomize, self.schedule)
        self.refresh_matches_tree()

    def refresh_matches_tree(self):
        self.matches_tree.delete(*self.matches_tree.get_children())
        for m in self.schedule['matches']:
            self.matches_tree.insert('', 'end', values=(m['team1'], m['team2'], 'Yes' if m.get('played') else 'No'))

    def refresh_games_trees(self):
        # Sync scores and statuses from MongoDB
        if self.schedule:
            self.schedule = sync_scores_from_mongodb(self.schedule)
        
        filter_text = self.filter_var.get().lower() if hasattr(self, 'filter_var') else ''
        self.scheduled_tree.delete(*self.scheduled_tree.get_children())
        self.completed_tree.delete(*self.completed_tree.get_children())
        for idx, m in enumerate(self.schedule['matches']):
            # Filtering
            if filter_text:
                if filter_text not in m['team1'].lower() and filter_text not in m['team2'].lower() and filter_text not in m.get('status', 'Not Started').lower():
                    continue
            vals = (
                idx,
                m['team1'],
                'Yes' if m.get('penalty_team1') else 'No',
                m['team2'],
                'Yes' if m.get('penalty_team2') else 'No',
                m.get('comments', ''),
                m.get('status', 'Not Started'),
                m.get('referee', ''),
                m.get('score1', ''),
                m.get('score2', ''),
                'Yes' if m.get('next_up', False) else ''
            )
            if m.get('played'):
                self.completed_tree.insert('', 'end', values=vals)
            else:
                self.scheduled_tree.insert('', 'end', values=vals)

    def toggle_played_scheduled(self):
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        m = get_match_data(idx, self.schedule)
        set_match_played(self.schedule, idx, not m.get('played', False))
        self.refresh_games_trees()

    def toggle_penalty_scheduled(self, team):
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        m = get_match_data(idx, self.schedule)
        if team == 1:
            set_match_penalty_for_team(idx, 1, not m.get('penalty_team1', False), self.schedule)
        elif team == 2:
            set_match_penalty_for_team(idx, 2, not m.get('penalty_team2', False), self.schedule)
        self.refresh_games_trees()

    def show_sched_menu(self, event):
        iid = self.scheduled_tree.identify_row(event.y)
        if iid:
            self.scheduled_tree.selection_set(iid)
            self.sched_menu.tk_popup(event.x_root, event.y_root)

    def show_comp_menu(self, event):
        iid = self.completed_tree.identify_row(event.y)
        if iid:
            self.completed_tree.selection_set(iid)
            self.comp_menu.tk_popup(event.x_root, event.y_root)

    def edit_status_scheduled(self):
        self._edit_status(self.scheduled_tree)
    def edit_status_completed(self):
        self._edit_status(self.completed_tree)
    def _edit_status(self, tree):
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])['values'][0])
        current = self.schedule['matches'][idx].get('status', 'Not Started')
        
        # Create a simple dropdown dialog
        dialog = tk.Toplevel(self)
        dialog.title('Edit Status')
        dialog.geometry('300x150')
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text='Select Status:').pack(pady=10)
        status_var = tk.StringVar(value=current)
        status_combo = ttk.Combobox(dialog, textvariable=status_var, values=MATCH_STATUSES, state='readonly')
        status_combo.pack(pady=10)
        
        def apply_status():
            new_status = status_var.get()
            if new_status in MATCH_STATUSES:
                self.schedule['matches'][idx]['status'] = new_status
                self.refresh_games_trees()
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='Apply', command=apply_status).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Cancel', command=cancel).pack(side='left', padx=5)

    def edit_referee_scheduled(self):
        self._edit_referee(self.scheduled_tree)
    def edit_referee_completed(self):
        self._edit_referee(self.completed_tree)
    def _edit_referee(self, tree):
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])['values'][0])
        current = self.schedule['matches'][idx].get('referee', '')
        new_ref = simpledialog.askstring('Edit Referee', f'Enter referee ({', '.join(REFEREES)}):', initialvalue=current)
        if new_ref:
            self.schedule['matches'][idx]['referee'] = new_ref
            self.refresh_games_trees()

    def edit_scores_scheduled(self):
        self._edit_scores(self.scheduled_tree)
    def edit_scores_completed(self):
        self._edit_scores(self.completed_tree)
    def _edit_scores(self, tree):
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])['values'][0])  # This is now the correct global match index
        m = self.schedule['matches'][idx]
        score1 = simpledialog.askinteger(
            'Edit Score',
            f"Enter score for {m['team1']} (current: {m.get('score1', '')}):",
            initialvalue=m.get('score1', 0)
        )
        score2 = simpledialog.askinteger(
            'Edit Score',
            f"Enter score for {m['team2']} (current: {m.get('score2', '')}):",
            initialvalue=m.get('score2', 0)
        )
        if score1 is not None:
            m['score1'] = score1
        if score2 is not None:
            m['score2'] = score2
        if score1 is not None and score2 is not None:
            m['played'] = True

        update_mongodb_from_schedule(self.schedule)
        self.refresh_games_trees()
        self.refresh_data()


    def set_next_up_scheduled(self):
        self._set_next_up(self.scheduled_tree)
    def set_next_up_completed(self):
        self._set_next_up(self.completed_tree)
    def _set_next_up(self, tree):
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])['values'][0])  # Correct match_id
        # Clear all previous next_up flags
        for m in self.schedule['matches']:
            m['next_up'] = False
        # Set the selected match as next up
        self.schedule['matches'][idx]['next_up'] = True

        # Save to MongoDB live_announcement collection
        match_data = self.schedule['matches'][idx].copy()
        match_data['timestamp'] = datetime.now().isoformat()
        live_announce_collection.delete_many({})
        live_announce_collection.insert_one(match_data)

        self.refresh_games_trees()


    def save_schedule(self):
        save_schedule(self.schedule)
        messagebox.showinfo('Saved', 'Schedule saved to file.')

    def save_games_schedule(self, show_popup=True):
        # Overwrite the schedule file with only the current matches (delete all previous schedules and write the new one)
        if not self.schedule or not self.schedule.get('matches'):
            if show_popup:
                messagebox.showwarning('No Schedule', 'No schedule to save.')
            return
        save_schedule(self.schedule)
        if show_popup:
            messagebox.showinfo('Saved', 'Schedule overwritten and saved to file.')
        self.refresh_comment_history()

    def load_schedule_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('JSON Files', '*.json')])
        if not file_path:
            return
        import json
        try:
            with open(file_path, 'r') as f:
                loaded = json.load(f)
            if 'matches' in loaded and 'teams' in loaded:
                self.schedule = loaded
                # Rebuild the Games tab
                for widget in self.games_frame.winfo_children():
                    widget.destroy()
                self.create_games_tab(self.games_frame)
                # Rebuild the Comment History tab
                for widget in self.comment_history_frame.winfo_children():
                    widget.destroy()
                self.create_comment_history_tab(self.comment_history_frame)
                messagebox.showinfo('Loaded', 'Schedule loaded successfully.')
            else:
                messagebox.showerror('Error', 'Invalid schedule file.')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load schedule: {e}')

    def edit_comment_scheduled(self):
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        current = get_match_comment_data(idx, self.schedule)
        new_comment = simpledialog.askstring('Edit Comment', 'Enter comment:', initialvalue=current)
        if new_comment is not None:
            # Save old comment to history if changed
            if new_comment != current:
                if 'comment_history' not in self.schedule['matches'][idx]:
                    self.schedule['matches'][idx]['comment_history'] = []
                add_comment_to_history(idx, current, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            set_match_comment_data(idx, new_comment, self.schedule)
            self.refresh_games_trees()
            self.refresh_comment_history()

    def edit_comment_completed(self):
        sel = self.completed_tree.selection()
        if not sel:
            return
        idx = int(self.completed_tree.item(sel[0])['values'][0])
        current = get_match_comment_data(idx, self.schedule)
        new_comment = simpledialog.askstring('Edit Comment', 'Enter comment:', initialvalue=current)
        if new_comment is not None:
            # Save old comment to history if changed
            if new_comment != current:
                if 'comment_history' not in self.schedule['matches'][idx]:
                    self.schedule['matches'][idx]['comment_history'] = []
                add_comment_to_history(idx, current, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            set_match_comment_data(idx, new_comment, self.schedule)
            self.refresh_games_trees()
            self.refresh_comment_history()

    def refresh_data(self):
        # Sync scores from MongoDB to schedule
        if self.schedule:
            self.schedule = sync_scores_from_mongodb(self.schedule)
        
        data = refresh_tournament_data()
        games = data['games']
        next_game = data['next_game']
        
        # Next game: use the first unplayed match from the schedule
        next_game_text = 'No upcoming games'
        # Automatically flag the first unplayed match as next_up
        updated = False
        for m in self.schedule.get('matches', []):
            if not m.get('played', False) and not updated:
                m['next_up'] = True
                updated = True
            else:
                m['next_up'] = False
        save_schedule(self.schedule)
        if self.schedule and self.schedule.get('matches'):
            for m in self.schedule['matches']:
                if not m.get('played'):
                    next_game_text = f"Next Game: {m['team1']} vs {m['team2']}"
                    break
        self.next_game_label.config(text=next_game_text)
        
        # Games table - show all teams from schedule and games
        for row in self.games_tree.get_children():
            self.games_tree.delete(row)
        
        # Get all teams that appear in both schedule and games
        all_teams = get_all_teams_from_schedule_and_games(self.schedule)
        
        # Show newest games first, one row per team per game
        for g in reversed(games):
            t1 = g.get('Team1', {})
            t2 = g.get('Team2', {})
            for team in [t1, t2]:
                # Get the latest timestamp for this team from score history
                latest_timestamp = ''
                if self.schedule and self.schedule.get('matches'):
                    for match in self.schedule['matches']:
                        if match.get('score_history'):
                            for hist in match['score_history']:
                                if hist.get('team1') == team.get('Name', '') or hist.get('team2') == team.get('Name', ''):
                                    if hist['timestamp'] > latest_timestamp:
                                        latest_timestamp = hist['timestamp']
                
                vals = [
                    g.get('GameNumber', ''),
                    g.get('timestamp', ''),
                    team.get('Name', ''),
                    team.get('Score', ''),
                    team.get('OrangeBalls', ''),
                    team.get('PurpleBalls', ''),
                    latest_timestamp
                ]
                self.games_tree.insert('', 'end', values=vals)
        self.games_tree.tag_configure('winner1', background='#d0ffd0')
        self.games_tree.tag_configure('winner2', background='#d0d0ff')
        
        # Leaderboard - show all teams with their scores
        for row in self.leaderboard_tree.get_children():
            self.leaderboard_tree.delete(row)
        
        # Calculate scores for all teams
        team_scores = {}
        for team in all_teams:
            if team:  # Skip empty team names
                team_scores[team] = 0
        
        # Sum up scores from MongoDB games
        for game in games:
            t1 = game.get('Team1', {})
            t2 = game.get('Team2', {})
            team1_name = t1.get('Name', '')
            team2_name = t2.get('Name', '')
            
            if team1_name in team_scores:
                team_scores[team1_name] += t1.get('Score', 0)
            if team2_name in team_scores:
                team_scores[team2_name] += t2.get('Score', 0)
        
        # Convert to list and sort by score (lowest first)
        leaderboard = [{'team': team, 'score': score} for team, score in team_scores.items()]
        leaderboard.sort(key=lambda x: x['score'])
        
        for i, entry in enumerate(leaderboard):
            # Get the latest timestamp for this team from score history
            latest_timestamp = ''
            if self.schedule and self.schedule.get('matches'):
                for match in self.schedule['matches']:
                    if match.get('score_history'):
                        for hist in match['score_history']:
                            if hist.get('team1') == entry['team'] or hist.get('team2') == entry['team']:
                                if hist['timestamp'] > latest_timestamp:
                                    latest_timestamp = hist['timestamp']
            
            row_id = self.leaderboard_tree.insert('', 'end', values=(entry['team'], entry['score'], latest_timestamp))
            if i == 0:
                self.leaderboard_tree.item(row_id, tags=('leader',))
        self.leaderboard_tree.tag_configure('leader', background='#fffacd')
    
    def schedule_auto_refresh(self):
        """Schedule the next auto-refresh"""
        if hasattr(self, 'auto_refresh_enabled') and self.auto_refresh_enabled:
            self.after(self.auto_refresh_interval * 1000, self.auto_refresh)
    
    def auto_refresh(self):
        """Perform auto-refresh and schedule the next one"""
        if hasattr(self, 'auto_refresh_enabled') and self.auto_refresh_enabled:
            self.refresh_data()
            self.schedule_auto_refresh()

    def export_excel(self):
        filename = export_excel()
        messagebox.showinfo('Exported', f'Exported to {filename}')

    def refresh_comment_history(self):
        if not hasattr(self, 'comment_tree'):
            return
        self.comment_tree.delete(*self.comment_tree.get_children())
        if not self.schedule or not self.schedule.get('matches'):
            return
        for idx, m in enumerate(self.schedule['matches']):
            for hist in m.get('comment_history', []):
                self.comment_tree.insert('', 'end', values=(
                    idx,
                    m['team1'],
                    m['team2'],
                    hist['comment'],
                    hist['timestamp']
                ))

    def save_team_notes(self):
        notes = self.notes_text.get('1.0', 'end').strip()
        if 'team_notes' not in self.schedule:
            self.schedule['team_notes'] = {}
        for team in self.schedule['teams']:
            self.schedule['team_notes'][team] = notes  # For demo, same notes for all; can be per-team
        save_team_notes(self.schedule['team_notes'])
        messagebox.showinfo('Saved', 'Team notes saved.')

    def refresh_team_notes(self):
        notes = load_team_notes()
        text = '\n'.join(f'{team}: {note}' for team, note in notes.items())
        self.notes_text.delete('1.0', 'end')
        self.notes_text.insert('1.0', text)

    def export_schedule_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV Files', '*.csv')])
        if not file_path:
            return
        filename = export_schedule_csv(self.schedule)
        messagebox.showinfo('Exported', f'Schedule exported to {filename}')

    def schedule_display_update(self):
        # Schedule the next display data update
        self.app_state.display_update_job = self.after(
            self.app_state.display_update_interval, 
            self.periodic_display_update
        )

    def periodic_display_update(self):
        from data.mongodb_client import publish_display_data, get_display_payload
        try:
            display_data = get_display_payload()
            publish_display_data(display_data)
        except Exception as e:
            print(f"Error publishing display data: {e}")
        self.schedule_display_update()

    def on_close(self):
        # Cancel display update job
        if self.app_state.display_update_job is not None:
            self.after_cancel(self.app_state.display_update_job)
            self.app_state.display_update_job = None
        
        result = messagebox.askyesnocancel('Save Before Exiting', 
                                        'Do you want to save all changes before exiting?')
        if result is None:
            return  # Cancel: do not close
        if result:
            save_settings(self.app_state.settings)
            self.games_tab.save_games_schedule(show_popup=False)
        self.destroy()

    def start_finals(self):
        # Get top teams by score
        from core.tournament_logic import get_team_scores_for_finals, create_finals_schedule
        top_teams = get_team_scores_for_finals(self.app_state.schedule)
        if len(top_teams) < 4:
            messagebox.showerror("Finals", "Not enough teams for finals.")
            return
        
        # Create finals schedule
        finals_schedule = create_finals_schedule(top_teams)
        if finals_schedule:
            self.app_state.schedule["finals"] = finals_schedule
            from core.match_scheduler import save_finals_schedule
            save_finals_schedule(finals_schedule)
            self.show_visual_finals_window()
        else:
            messagebox.showerror("Finals", "Could not create finals schedule.")

    def show_visual_finals_window(self):
        FinalsBracket(self, self.app_state.schedule, self.app_state.settings)

    def upload_display_now(self):
        from data.mongodb_client import publish_display_data
        try:
            publish_display_data()
            messagebox.showinfo('Display Upload', 'Display data uploaded successfully!')
        except Exception as e:
            messagebox.showerror('Display Upload', f'Error uploading display data: {e}')

class FinalsBracket(tk.Toplevel):
    def __init__(self, parent, schedule, settings):
        super().__init__(parent)
        self.parent = parent
        self.schedule = schedule
        self.settings = settings

        self.title("SCORIX Finals Bracket")
        self.geometry("850x600")

        self.canvas = tk.Canvas(self, bg=self.settings.get("theme_color", "#f0f0f0"))
        self.canvas.pack(fill="both", expand=True)

        self.BOX_WIDTH = 180
        self.BOX_HEIGHT = 45
        self.WIN_COLOR = "#d4edda"
        self.LOSE_COLOR = "#f8d7da"
        self.NORMAL_COLOR = "#ffffff"
        self.HOVER_COLOR = "#e2e6ea"

        self.draw_bracket()

    def draw_bracket(self):
        self.canvas.delete("all")
        semifinals = [m for m in self.schedule.get('finals', []) if m['round'] == 'semifinal']
        if not semifinals:
            return

        sf1_y, sf2_y = 150, 450
        final_y = (sf1_y + sf2_y) / 2
        third_y = final_y + 120
        col1_x, col2_x, col3_x = 20, 320, 620

        # Draw Bracket Structure
        self.canvas.create_line(col1_x + self.BOX_WIDTH, sf1_y, col2_x, sf1_y, width=2)
        self.canvas.create_line(col1_x + self.BOX_WIDTH, sf2_y, col2_x, sf2_y, width=2)
        self.canvas.create_line(col2_x, sf1_y, col2_x, sf2_y, width=2)
        self.canvas.create_line(col2_x + self.BOX_WIDTH, final_y, col3_x, final_y, width=2)
        self.canvas.create_line(col2_x + self.BOX_WIDTH, third_y, col2_x + self.BOX_WIDTH + 50, third_y, width=2)

        # Draw Titles
        self.canvas.create_text(col1_x + self.BOX_WIDTH / 2, 50, text="Semifinals", font=("Arial", 14, "bold"))
        self.canvas.create_text(col2_x + self.BOX_WIDTH / 2, 50, text="Final", font=("Arial", 14, "bold"))
        self.canvas.create_text(col3_x + 20, 50, text="Champion", font=("Arial", 14, "bold"), anchor="w")
        self.canvas.create_text(col2_x + self.BOX_WIDTH / 2, third_y - 60, text="3rd Place Match", font=("Arial", 12, "bold"))

        # Draw Matches
        sf1, sf2 = semifinals[0], semifinals[1]
        self.draw_match(col1_x, sf1_y, sf1)
        self.draw_match(col1_x, sf2_y, sf2)

        if "winner" in sf1 and "winner" in sf2:
            winner1, loser1 = (sf1["team1"], sf1["team2"]) if sf1["winner"] == sf1["team1"] else (sf1["team2"], sf1["team1"])
            winner2, loser2 = (sf2["team1"], sf2["team2"]) if sf2["winner"] == sf2["team1"] else (sf2["team2"], sf2["team1"])
            self.draw_match(col2_x, final_y, {"team1": winner1, "team2": winner2, "round": "final"})
            self.draw_match(col2_x, third_y, {"team1": loser1, "team2": loser2, "round": "third"})

        if self.schedule.get("champion"):
            self.canvas.create_text(col3_x, final_y, text=self.schedule["champion"], font=("Arial", 16, "bold"), fill="gold", anchor="w")
        if self.schedule.get("third_place"):
            self.canvas.create_text(col2_x + self.BOX_WIDTH + 60, third_y, text=self.schedule["third_place"], font=("Arial", 12, "bold"), fill="orange", anchor="w")

    def draw_match(self, x, y, match):
        t1, t2 = match["team1"], match["team2"]
        winner = self.schedule.get("champion") if match["round"] == "final" else self.schedule.get("third_place") if match["round"] == "third" else match.get("winner")

        padding = 10
        self._draw_team_box(x, y - self.BOX_HEIGHT / 2 - padding, t1, winner, match)
        self._draw_team_box(x, y + self.BOX_HEIGHT / 2 + padding, t2, winner, match)

    def _draw_team_box(self, x, y, team, winner, match):
        y_top = y - self.BOX_HEIGHT / 2
        y_bottom = y + self.BOX_HEIGHT / 2

        is_clickable = winner is None
        bg_color = self.NORMAL_COLOR
        if winner:
            bg_color = self.WIN_COLOR if team == winner else self.LOSE_COLOR

        box_tag = f"box_{team}_{match['round']}"
        text_tag = f"text_{team}_{match['round']}"
        group_tag = f"group_{team}_{match['round']}"

        box_id = self.canvas.create_rectangle(x, y_top, x + self.BOX_WIDTH, y_bottom, fill=bg_color, outline="black", width=1.5, tags=(box_tag, group_tag))
        text_id = self.canvas.create_text(x + self.BOX_WIDTH / 2, y, text=team, font=("Arial", 12), tags=(text_tag, group_tag))

        if is_clickable:
            self.canvas.tag_bind(group_tag, "<Button-1>", lambda e: self.set_winner(match, team))
            self.canvas.tag_bind(group_tag, "<Enter>", lambda e: self.canvas.itemconfig(box_tag, fill=self.HOVER_COLOR))
            self.canvas.tag_bind(group_tag, "<Leave>", lambda e: self.canvas.itemconfig(box_tag, fill=self.NORMAL_COLOR))

    def set_winner(self, match, winner):
        if match["round"] == "semifinal":
            for m in self.schedule.get("finals", []):
                if m["team1"] == match["team1"] and m["team2"] == match["team2"]:
                    m["winner"] = winner
                    break
        elif match["round"] == "final":
            self.schedule["champion"] = winner
        elif match["round"] == "third":
            self.schedule["third_place"] = winner
        self.draw_bracket()

if __name__ == '__main__':
    app = TournamentApp()
    app.mainloop() 