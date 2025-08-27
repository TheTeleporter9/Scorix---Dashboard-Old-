"""
Scores tab functionality for the tournament application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils.excel_exporter import export_games_to_excel
from data.mongodb_client import publish_display_data
from .app_state import sync_scores_from_mongodb, get_all_teams_from_schedule_and_games

class ScoresTab:
    def __init__(self, parent, app_state):
        self.parent = parent
        self.app_state = app_state
        self.schedule = app_state.schedule
        self.settings = app_state.settings
        self.create_widgets()
        
    def create_widgets(self):
        # CJM label in corner
        cjm_label = tk.Label(self.parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        
        # Next game label
        self.next_game_label = tk.Label(self.parent, text='', font=('Arial', 16, 'bold'), bg=self.settings['theme_color'])
        self.next_game_label.pack(pady=10)

        # Games frame
        games_frame = tk.LabelFrame(self.parent, text='Games Played', font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
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
        leaderboard_frame = tk.LabelFrame(self.parent, text='Leaderboard', font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
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
        btn_frame = tk.Frame(self.parent, bg=self.settings['theme_color'])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='Refresh', command=self.refresh_data, bg='#4CAF50', fg='white', 
                font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        tk.Button(btn_frame, text='Export to Excel', command=self.export_excel, bg='#2196F3', fg='white', 
                font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        tk.Button(btn_frame, text='Upload Display Now', command=self.upload_display_now, bg='#FF9800', fg='white', 
                font=('Arial', 12, 'bold')).pack(side='left', padx=10)

    def refresh_data(self):
        # Sync scores from MongoDB to schedule
        if self.schedule:
            self.schedule = sync_scores_from_mongodb(self.schedule)
        
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

        if self.schedule and self.schedule.get('matches'):
            for m in self.schedule['matches']:
                if not m.get('played'):
                    next_game_text = f"Next Game: {m['team1']} vs {m['team2']}"
                    break
        self.next_game_label.config(text=next_game_text)

        # Clear games tree
        for row in self.games_tree.get_children():
            self.games_tree.delete(row)

        # Get all teams that appear in both schedule and games
        all_teams = get_all_teams_from_schedule_and_games(self.schedule)

        # Calculate scores for all teams
        team_scores = {team: 0 for team in all_teams if team}

        # Update games tree and calculate scores
        from data.mongodb_client import get_all_games
        games = get_all_games()
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

                # Update team scores
                team_name = team.get('Name', '')
                if team_name in team_scores:
                    team_scores[team_name] += team.get('Score', 0)

        self.games_tree.tag_configure('winner1', background='#d0ffd0')
        self.games_tree.tag_configure('winner2', background='#d0d0ff')

        # Update leaderboard
        for row in self.leaderboard_tree.get_children():
            self.leaderboard_tree.delete(row)

        # Sort teams by score
        leaderboard = [{'team': team, 'score': score} for team, score in team_scores.items()]
        leaderboard.sort(key=lambda x: x['score'], reverse=True)

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

    def export_excel(self):
        filename = export_games_to_excel()
        messagebox.showinfo('Exported', f'Exported to {filename}')

    def upload_display_now(self):
        try:
            publish_display_data()
            messagebox.showinfo('Display Upload', 'Display data uploaded successfully!')
        except Exception as e:
            messagebox.showerror('Display Upload', f'Error uploading display data: {e}')
