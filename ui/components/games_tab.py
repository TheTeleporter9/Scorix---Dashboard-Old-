"""
Games tab functionality for the tournament application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
from data.db_utils import sync_scores_from_mongodb
from core.match_scheduler import (
    get_match, set_match_played, set_match_penalty,
    set_match_comment, get_match_comment, save_schedule,
    load_schedule
)

MATCH_STATUSES = ['Not Started', 'In Progress', 'Completed', 'Cancelled', 'Postponed']
REFEREES = ['Referee 1', 'Referee 2', 'Referee 3', 'Referee 4']

class GamesTab:
    def __init__(self, parent, app_state):
        self.parent = parent
        self.app_state = app_state
        self.schedule = app_state.schedule
        self.settings = app_state.settings
        self.create_widgets()

    def create_widgets(self):
        # Safety check: if no schedule loaded, show warning and disable controls
        if not self.schedule or not self.schedule.get('matches'):
            warning = tk.Label(self.parent, text='No schedule loaded. Please load or create a schedule first.',
                           fg='red', font=('Arial', 14), bg=self.settings['theme_color'])
            warning.pack(pady=20)
            load_btn = tk.Button(self.parent, text='Load Schedule', command=self.load_schedule_from_file)
            load_btn.pack(pady=10)
            self.scheduled_tree = None
            self.completed_tree = None
            return

        # Scheduled games (not played)
        scheduled_frame = tk.LabelFrame(self.parent, text='Scheduled Games', font=('Arial', 12, 'bold'), bg='#e0f7fa')
        scheduled_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.scheduled_tree = ttk.Treeview(scheduled_frame, columns=(
            'Index', 'Team 1', 'Penalty 1', 'Team 2', 'Penalty 2', 'Comments', 'Status', 'Referee',
            'Score 1', 'Score 2', 'Next Up'), show='headings', height=10)
        for col in self.scheduled_tree['columns']:
            self.scheduled_tree.heading(col, text=col)
            self.scheduled_tree.column(col, anchor='center', width=100)
        self.scheduled_tree.pack(fill='both', expand=True)

        # Completed games (played)
        completed_frame = tk.LabelFrame(self.parent, text='Completed Games', font=('Arial', 12, 'bold'), bg='#ffe0b2')
        completed_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.completed_tree = ttk.Treeview(completed_frame, columns=(
            'Index', 'Team 1', 'Penalty 1', 'Team 2', 'Penalty 2', 'Comments', 'Status', 'Referee',
            'Score 1', 'Score 2', 'Next Up'), show='headings', height=10)
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
        filter_frame = tk.Frame(self.parent, bg=self.settings['theme_color'])
        filter_frame.pack(fill='x', padx=10, pady=2)
        tk.Label(filter_frame, text='Filter by Team or Status:', bg=self.settings['theme_color']).pack(side='left')
        self.filter_var = tk.StringVar()
        filter_entry = tk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.pack(side='left', padx=5)
        tk.Button(filter_frame, text='Apply Filter', command=self.refresh_games_trees).pack(side='left', padx=5)

        # Controls
        control_frame = tk.Frame(self.parent, bg=self.settings['theme_color'])
        control_frame.pack(pady=10)
        tk.Label(control_frame, text='Select a scheduled game and:', bg=self.settings['theme_color']).pack(side='left')
        tk.Button(control_frame, text='Toggle Played', command=self.toggle_played_scheduled).pack(side='left', padx=5)
        tk.Button(control_frame, text='Toggle Penalty Team 1',
                command=lambda: self.toggle_penalty_scheduled(1)).pack(side='left', padx=5)
        tk.Button(control_frame, text='Toggle Penalty Team 2',
                command=lambda: self.toggle_penalty_scheduled(2)).pack(side='left', padx=5)
        tk.Button(control_frame, text='Save Changes', command=self.save_games_schedule).pack(side='left', padx=5)
        tk.Button(control_frame, text='Load Schedule', command=self.load_schedule_from_file).pack(side='left', padx=5)

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
                if (filter_text not in m['team1'].lower() and 
                    filter_text not in m['team2'].lower() and 
                    filter_text not in m.get('status', 'Not Started').lower()):
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

    def show_sched_menu(self, event):
        if not self.scheduled_tree:
            return
        iid = self.scheduled_tree.identify_row(event.y)
        if iid:
            self.scheduled_tree.selection_set(iid)
            self.sched_menu.tk_popup(event.x_root, event.y_root)

    def show_comp_menu(self, event):
        if not self.completed_tree:
            return
        iid = self.completed_tree.identify_row(event.y)
        if iid:
            self.completed_tree.selection_set(iid)
            self.comp_menu.tk_popup(event.x_root, event.y_root)

    def view_comment_scheduled(self):
        if not self.scheduled_tree:
            return
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        comment = get_match_comment(self.schedule, idx)
        messagebox.showinfo('Comment', comment if comment else 'No comment.')

    def edit_comment_scheduled(self):
        if not self.scheduled_tree:
            return
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        current = get_match_comment(self.schedule, idx)
        new_comment = simpledialog.askstring('Edit Comment', 'Enter comment:', initialvalue=current)
        if new_comment is not None:
            # Save old comment to history if changed
            if new_comment != current:
                self.schedule['matches'][idx]['comment_history'].append({
                    'comment': current,
                    'timestamp': datetime.now().isoformat()
                })
            set_match_comment(self.schedule, idx, new_comment)
            self.refresh_games_trees()

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
        dialog = tk.Toplevel(self.parent)
        dialog.title('Edit Status')
        dialog.geometry('300x150')
        dialog.transient(self.parent)
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

    def toggle_played_scheduled(self):
        if not self.scheduled_tree:
            return
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        match = get_match(self.schedule, idx)
        set_match_played(self.schedule, idx, not match.get('played', False))
        self.refresh_games_trees()

    def toggle_penalty_scheduled(self, team_num):
        if not self.scheduled_tree:
            return
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        match = get_match(self.schedule, idx)
        penalty_key = f"penalty_team{team_num}"
        current_penalty = match.get(penalty_key, False)
        set_match_penalty(self.schedule, idx, team_num, not current_penalty)
        self.refresh_games_trees()

    def edit_referee_scheduled(self):
        if not self.scheduled_tree:
            return
        self._edit_referee(self.scheduled_tree)

    def edit_referee_completed(self):
        if not self.completed_tree:
            return
        self._edit_referee(self.completed_tree)

    def _edit_referee(self, tree):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])['values'][0])
        current = self.schedule['matches'][idx].get('referee', '')
        new_referee = simpledialog.askstring('Edit Referee', 'Enter referee:', initialvalue=current)
        if new_referee is not None:
            self.schedule['matches'][idx]['referee'] = new_referee
            self.refresh_games_trees()

    def edit_scores_scheduled(self):
        if not self.scheduled_tree:
            return
        self._edit_scores(self.scheduled_tree)

    def edit_scores_completed(self):
        if not self.completed_tree:
            return
        self._edit_scores(self.completed_tree)

    def _edit_scores(self, tree):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])['values'][0])
        match = self.schedule['matches'][idx]
        current_score1 = match.get('score1', '')
        current_score2 = match.get('score2', '')
        
        dialog = tk.Toplevel(self.parent)
        dialog.title('Edit Scores')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"{match['team1']} Score:").pack(pady=5)
        score1_var = tk.StringVar(value=str(current_score1))
        tk.Entry(dialog, textvariable=score1_var).pack(pady=5)
        
        tk.Label(dialog, text=f"{match['team2']} Score:").pack(pady=5)
        score2_var = tk.StringVar(value=str(current_score2))
        tk.Entry(dialog, textvariable=score2_var).pack(pady=5)
        
        def apply_scores():
            try:
                new_score1 = int(score1_var.get())
                new_score2 = int(score2_var.get())
                self.schedule['matches'][idx]['score1'] = new_score1
                self.schedule['matches'][idx]['score2'] = new_score2
                self.refresh_games_trees()
                dialog.destroy()
            except ValueError:
                messagebox.showerror('Error', 'Please enter valid numbers for scores.')
        
        def cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='Apply', command=apply_scores).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Cancel', command=cancel).pack(side='left', padx=5)

    def set_next_up_scheduled(self):
        if not self.scheduled_tree:
            return
        self._set_next_up(self.scheduled_tree)

    def set_next_up_completed(self):
        if not self.completed_tree:
            return
        self._set_next_up(self.completed_tree)

    def _set_next_up(self, tree):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])['values'][0])
        # Reset all next_up flags
        for match in self.schedule['matches']:
            match['next_up'] = False
        # Set selected match as next_up
        self.schedule['matches'][idx]['next_up'] = True
        self.refresh_games_trees()

    def view_comment_completed(self):
        if not self.completed_tree:
            return
        sel = self.completed_tree.selection()
        if not sel:
            return
        idx = int(self.completed_tree.item(sel[0])['values'][0])
        comment = get_match_comment(self.schedule, idx)
        messagebox.showinfo('Comment', comment if comment else 'No comment.')

    def edit_comment_completed(self):
        if not self.completed_tree:
            return
        sel = self.completed_tree.selection()
        if not sel:
            return
        idx = int(self.completed_tree.item(sel[0])['values'][0])
        current = get_match_comment(self.schedule, idx)
        new_comment = simpledialog.askstring('Edit Comment', 'Enter comment:', initialvalue=current)
        if new_comment is not None:
            set_match_comment(self.schedule, idx, new_comment)
            self.refresh_games_trees()

    def save_games_schedule(self, show_popup=True):
        if not self.schedule or not self.schedule.get('matches'):
            if show_popup:
                messagebox.showwarning('No Schedule', 'No schedule to save.')
            return
        save_schedule(self.schedule)
        if show_popup:
            messagebox.showinfo('Saved', 'Schedule overwritten and saved to file.')

    def load_schedule_from_file(self):
        try:
            loaded_schedule = load_schedule()
            if loaded_schedule:
                self.schedule = loaded_schedule
                # Rebuild the Games tab
                for widget in self.parent.winfo_children():
                    widget.destroy()
                self.create_widgets()
            messagebox.showinfo('Loaded', 'Schedule loaded successfully.')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load schedule: {e}')
