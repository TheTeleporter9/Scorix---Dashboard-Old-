"""
Operator tab functionality for the tournament application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.match_scheduler import (
    add_team, remove_team, set_num_matches, generate_round_robin,
    save_schedule
)
from core.team_notes import load_team_notes, save_team_notes

class OperatorTab:
    def __init__(self, parent, app_state):
        self.parent = parent
        self.app_state = app_state
        self.schedule = app_state.schedule
        self.settings = app_state.settings
        self.randomization_type = tk.StringVar(value="shuffle") # Default randomization type
        self.random_seed = tk.StringVar(value="") # Seed for seeded randomization
        self.create_widgets()
        
    def refresh_data(self):
        """Refresh the operator tab data."""
        pass  # No data needs to be refreshed in this tab

    def create_widgets(self):
        # CJM label in corner
        cjm_label = tk.Label(self.parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')

        # Teams management
        teams_frame = tk.LabelFrame(self.parent, text='Teams', font=('Arial', 12, 'bold'),
                                bg=self.settings['theme_color'])
        teams_frame.pack(fill='x', padx=10, pady=5)
        
        self.teams_listbox = tk.Listbox(teams_frame, height=6)
        self.teams_listbox.pack(side='left', padx=5, pady=5)
        self.refresh_teams_listbox()
        
        team_entry = tk.Entry(teams_frame)
        team_entry.pack(side='left', padx=5)
        
        tk.Button(teams_frame, text='Add Team',
                command=lambda: self.add_team(team_entry.get())).pack(side='left', padx=5)
        tk.Button(teams_frame, text='Remove Team',
                command=self.remove_selected_team).pack(side='left', padx=5)

        # Number of matches
        matches_frame = tk.Frame(self.parent, bg=self.settings['theme_color'])
        matches_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(matches_frame, text='Matches per team:',
              bg=self.settings['theme_color']).pack(side='left')
        
        self.num_matches_var = tk.IntVar(value=1)
        matches_entry = tk.Entry(matches_frame, textvariable=self.num_matches_var, width=5)
        matches_entry.pack(side='left', padx=5)
        
        tk.Button(matches_frame, text='Set',
                command=self.set_num_matches).pack(side='left', padx=5)
        tk.Button(matches_frame, text='Auto-generate Schedule',
                command=self.auto_generate_schedule).pack(side='left', padx=5)

        # Randomization type selection
        randomization_frame = tk.Frame(self.parent, bg=self.settings['theme_color'])
        randomization_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(randomization_frame, text='Randomization Type:',
                bg=self.settings['theme_color']).pack(side='left')
        
        randomization_options = ["shuffle", "seeded"]
        self.randomization_combobox = ttk.Combobox(randomization_frame,
                                                    textvariable=self.randomization_type,
                                                    values=randomization_options,
                                                    state="readonly")
        self.randomization_combobox.pack(side='left', padx=5)
        self.randomization_combobox.bind('<<ComboboxSelected>>', self.on_randomization_type_change)

        self.seed_label = tk.Label(randomization_frame, text='Seed:',
                                    bg=self.settings['theme_color'])
        self.seed_entry = tk.Entry(randomization_frame, textvariable=self.random_seed, width=10)
        
        self.on_randomization_type_change() # Initialize visibility of seed widgets

        # Matches table
        matches_table_frame = tk.LabelFrame(self.parent, text='Scheduled Matches',
                                        font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
        matches_table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.matches_tree = ttk.Treeview(matches_table_frame,
                                      columns=('Team 1', 'Team 2', 'Played'),
                                      show='headings',
                                      height=10)
        for col in self.matches_tree['columns']:
            self.matches_tree.heading(col, text=col)
            self.matches_tree.column(col, anchor='center', width=150)
        self.matches_tree.pack(fill='both', expand=True)
        self.refresh_matches_tree()

        # Save button
        tk.Button(self.parent, text='Save Schedule',
                command=self.save_schedule).pack(pady=10)

        # Team notes
        notes_frame = tk.LabelFrame(self.parent, text='Team Notes',
                                font=('Arial', 12, 'bold'), bg=self.settings['theme_color'])
        notes_frame.pack(fill='x', padx=10, pady=5)
        
        self.notes_text = tk.Text(notes_frame, height=4, width=60)
        self.notes_text.pack(side='left', padx=5)
        
        tk.Button(notes_frame, text='Save Notes',
                command=self.save_team_notes).pack(side='left', padx=5)
        self.refresh_team_notes()

    def refresh_teams_listbox(self):
        self.teams_listbox.delete(0, tk.END)
        for team in self.schedule['teams']:
            self.teams_listbox.insert(tk.END, team)

    def refresh_matches_tree(self):
        self.matches_tree.delete(*self.matches_tree.get_children())
        for m in self.schedule['matches']:
            self.matches_tree.insert('', 'end',
                                 values=(m['team1'], m['team2'],
                                       'Yes' if m.get('played') else 'No'))

    def refresh_team_notes(self):
        notes = load_team_notes()
        text = '\n'.join(f'{team}: {note}' for team, note in notes.items())
        self.notes_text.delete('1.0', 'end')
        self.notes_text.insert('1.0', text)

    def on_randomization_type_change(self, event=None):
        if self.randomization_type.get() == "seeded":
            self.seed_label.pack(side='left', padx=5)
            self.seed_entry.pack(side='left', padx=5)
        else:
            self.seed_label.pack_forget()
            self.seed_entry.pack_forget()

    def add_team(self, team_name):
        if not team_name.strip():
            return
        seed = int(self.random_seed.get()) if self.random_seed.get() else None
        add_team(team_name.strip(), self.schedule, self.randomization_type.get(), seed)
        self.refresh_teams_listbox()
        self.refresh_matches_tree()

    def remove_selected_team(self):
        selection = self.teams_listbox.curselection()
        if not selection:
            return
        team = self.teams_listbox.get(selection[0])
        seed = int(self.random_seed.get()) if self.random_seed.get() else None
        remove_team(team, self.schedule, self.randomization_type.get(), seed)
        self.refresh_teams_listbox()
        self.refresh_matches_tree()

    def set_num_matches(self):
        try:
            n = int(self.num_matches_var.get())
            seed = int(self.random_seed.get()) if self.random_seed.get() else None
            set_num_matches(self.schedule, n, self.randomization_type.get(), seed)
            self.refresh_matches_tree()
        except ValueError:
            messagebox.showerror('Error', 'Invalid number of matches or seed')

    def auto_generate_schedule(self):
        seed = int(self.random_seed.get()) if self.random_seed.get() else None
        generate_round_robin(self.schedule['teams'],
                             self.num_matches_var.get(),
                             self.randomization_type.get(),
                             seed)
        self.refresh_matches_tree()

    def save_schedule(self):
        save_schedule(self.schedule)
        messagebox.showinfo('Saved', 'Schedule saved to file.')

    def save_team_notes(self):
        notes = self.notes_text.get('1.0', 'end').strip()
        if 'team_notes' not in self.schedule:
            self.schedule['team_notes'] = {}
        for team in self.schedule['teams']:
            self.schedule['team_notes'][team] = notes  # For demo, same notes for all
        save_team_notes(self.schedule['team_notes'])
