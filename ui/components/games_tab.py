"""
Games tab functionality for the tournament application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
from core.match_scheduler import (
    get_match, set_match_played, set_match_penalty, set_match_comment, get_match_comment,
    save_schedule_to_file, load_schedule_from_file, get_match_data,
    set_match_penalty_for_team, set_match_status, set_match_referee, set_match_comment_data,
    add_comment_to_history, save_schedule, sync_scores_from_mongodb
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
        iid = self.scheduled_tree.identify_row(event.y)
        if iid:
            self.scheduled_tree.selection_set(iid)
            self.sched_menu.tk_popup(event.x_root, event.y_root)

    def show_comp_menu(self, event):
        iid = self.completed_tree.identify_row(event.y)
        if iid:
            self.completed_tree.selection_set(iid)
            self.comp_menu.tk_popup(event.x_root, event.y_root)

    def view_comment_scheduled(self):
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        comment = get_match_comment(idx)
        messagebox.showinfo('Comment', comment if comment else 'No comment.')

    def edit_comment_scheduled(self):
        sel = self.scheduled_tree.selection()
        if not sel:
            return
        idx = int(self.scheduled_tree.item(sel[0])['values'][0])
        current = get_match_comment(idx)
        new_comment = simpledialog.askstring('Edit Comment', 'Enter comment:', initialvalue=current)
        if new_comment is not None:
            # Save old comment to history if changed
            if new_comment != current:
                add_comment_to_history(idx, current, datetime.now())
            set_match_comment(idx, new_comment)
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

    def save_games_schedule(self, show_popup=True):
        if not self.schedule or not self.schedule.get('matches'):
            if show_popup:
                messagebox.showwarning('No Schedule', 'No schedule to save.')
            return
        save_schedule_to_file(self.schedule)
        if show_popup:
            messagebox.showinfo('Saved', 'Schedule overwritten and saved to file.')

    def load_schedule_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('JSON Files', '*.json')])
        if not file_path:
            return
        try:
            self.schedule = load_schedule_from_file(file_path)
            # Rebuild the Games tab
            for widget in self.parent.winfo_children():
                widget.destroy()
            self.create_widgets()
            messagebox.showinfo('Loaded', 'Schedule loaded successfully.')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load schedule: {e}')
