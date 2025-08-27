"""
Comment history tab functionality for the tournament application.
"""

import tkinter as tk
from tkinter import ttk

class CommentHistoryTab:
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
        
        tk.Label(self.parent, text='Comment History', font=('Arial', 16, 'bold'),
              bg=self.settings['theme_color']).pack(pady=10)
        
        self.comment_tree = ttk.Treeview(self.parent,
                                       columns=('Match', 'Team 1', 'Team 2', 'Old Comment', 'Timestamp'),
                                       show='headings',
                                       height=20)
        
        for col in self.comment_tree['columns']:
            self.comment_tree.heading(col, text=col)
            self.comment_tree.column(col, anchor='center', width=180)
        
        self.comment_tree.pack(fill='both', expand=True)
        self.refresh_comment_history()

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
