"""
Settings tab functionality for the tournament application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .app_state import load_comp_display_settings, save_comp_display_settings, save_settings

class SettingsTab:
    def __init__(self, parent, app_state):
        self.parent = parent
        self.app_state = app_state
        self.settings = app_state.settings
        self.create_widgets()
        
    def create_widgets(self):
        # CJM label in corner
        cjm_label = tk.Label(self.parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        tk.Label(self.parent, text='Settings', font=('Arial', 16, 'bold'), bg=self.settings['theme_color']).pack(pady=10)

        # Theme color
        tk.Label(self.parent, text='Theme Color:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        color_var = tk.StringVar(value=self.settings.get('theme_color', '#e3f2fd'))
        color_menu = ttk.Combobox(self.parent, textvariable=color_var, 
                                values=['#e3f2fd', '#fce4ec', '#fffde7', '#e8f5e9', '#ede7f6', '#fff3e0'], 
                                state='readonly')
        color_menu.pack(anchor='w', padx=40, pady=2)

        # Default matches per team
        tk.Label(self.parent, text='Default Matches per Team:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        matches_var = tk.IntVar(value=self.settings.get('default_matches_per_team', 1))
        matches_entry = tk.Entry(self.parent, textvariable=matches_var, width=5)
        matches_entry.pack(anchor='w', padx=40, pady=2)

        # Randomize schedule
        rand_var = tk.BooleanVar(value=self.settings.get('randomize_schedule', True))
        rand_check = tk.Checkbutton(self.parent, text='Randomize Schedule Order', variable=rand_var, 
                                bg=self.settings['theme_color'])
        rand_check.pack(anchor='w', padx=20, pady=2)

        # Enable Dark Mode
        tk.Label(self.parent, text='Enable Dark Mode:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        dark_var = tk.BooleanVar(value=self.settings.get('dark_mode', False))
        dark_check = tk.Checkbutton(self.parent, text='Enable Dark Mode', variable=dark_var, 
                                bg=self.settings['theme_color'])
        dark_check.pack(anchor='w', padx=40, pady=2)

        # Notification Sound
        tk.Label(self.parent, text='Notification Sound:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        notif_var = tk.BooleanVar(value=self.settings.get('notification_sound', True))
        notif_check = tk.Checkbutton(self.parent, text='Play sound on event', variable=notif_var, 
                                    bg=self.settings['theme_color'])
        notif_check.pack(anchor='w', padx=40, pady=2)

        # Font size
        tk.Label(self.parent, text='Font Size:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        font_var = tk.IntVar(value=self.settings.get('font_size', 12))
        font_entry = tk.Entry(self.parent, textvariable=font_var, width=5)
        font_entry.pack(anchor='w', padx=40, pady=2)

        # Display settings section
        display_var = tk.BooleanVar(value=False)
        def toggle_display():
            if display_var.get():
                display_frame.pack(fill='x', padx=20, pady=10)
            else:
                display_frame.pack_forget()

        display_check = tk.Checkbutton(self.parent, text='Show Display Settings', variable=display_var,
                                    command=toggle_display, bg=self.settings['theme_color'])
        display_check.pack(anchor='w', padx=20, pady=10)

        display_frame = tk.Frame(self.parent, bg=self.settings['theme_color'])
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
            save_settings(self.settings)

            # Save display MongoDB settings if visible
            if display_var.get():
                save_comp_display_settings({
                    'DISPLAY_MONGO_URI': disp_uri_var.get(),
                    'DISPLAY_DB_NAME': disp_db_var.get(),
                    'DISPLAY_COLLECTION_NAME': disp_coll_var.get(),
                })

            # Apply the theme
            self.app_state.apply_theme()
            messagebox.showinfo('Settings', 'Settings saved and theme applied!')

        tk.Button(self.parent, text='💾 Save Settings', command=save_and_apply,
                bg='#90caf9', fg='black').pack(pady=10)
