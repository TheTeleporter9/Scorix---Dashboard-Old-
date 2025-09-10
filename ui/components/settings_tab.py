"""
Settings tab functionality for the tournament application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .app_state import load_comp_display_settings, save_comp_display_settings, save_settings
from data.mongodb_client import run_server_in_thread as run_server
import random

class SettingsTab:
    def __init__(self, parent, app_state, apply_theme_callback):
        self.parent = parent
        self.app_state = app_state
        self.settings = app_state.settings
        self.apply_theme_callback = apply_theme_callback # Callback to apply theme to main app
        self.theme_colors = ['#e3f2fd', '#fce4ec', '#fffde7', '#e8f5e9', '#ede7f6', '#fff3e0'] # Define available themes
        self.create_widgets()
        
    def create_widgets(self):
        # CJM label in corner
        cjm_label = tk.Label(self.parent, text='CJM', font=('Arial', 8), bg=self.settings['theme_color'])
        cjm_label.place(relx=1.0, rely=0.0, anchor='ne')
        tk.Label(self.parent, text='Settings', font=('Arial', 16, 'bold'), bg=self.settings['theme_color']).pack(pady=10)

        # Theme color
        tk.Label(self.parent, text='Theme Color:', bg=self.settings['theme_color']).pack(anchor='w', padx=20)
        color_var = tk.StringVar(value=self.settings.get('theme_color', '#e3f2fd'))
        self.color_menu = ttk.Combobox(self.parent, textvariable=color_var, 
                                values=self.theme_colors, 
                                state='readonly')
        self.color_menu.pack(anchor='w', padx=40, pady=2)

        # Random Theme button
        tk.Button(self.parent, text='🎲 Random Theme', command=self.set_random_theme,
                bg='#a7c3d2', fg='black').pack(anchor='w', padx=40, pady=5)

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
            self.apply_theme_callback()
            messagebox.showinfo('Settings', 'Settings saved and theme applied!')

        tk.Button(self.parent, text='💾 Save Settings', command=save_and_apply,
                bg='#90caf9', fg='black').pack(pady=10)
                
        # Server settings section
        server_frame = tk.LabelFrame(self.parent, text="TCP Server Settings", bg=self.settings['theme_color'])
        server_frame.pack(fill='x', padx=20, pady=10)

        # IP Address
        ip_frame = tk.Frame(server_frame, bg=self.settings['theme_color'])
        ip_frame.pack(fill='x', padx=5, pady=5)
        
        self.ip_var = tk.StringVar(value='')
        self.auto_ip_var = tk.BooleanVar(value=True)
        
        def toggle_ip_entry(*args):
            if self.auto_ip_var.get():
                ip_entry.configure(state='disabled')
                self.ip_var.set('')
            else:
                ip_entry.configure(state='normal')

        tk.Label(ip_frame, text='Server IP:', bg=self.settings['theme_color']).pack(side='left', padx=5)
        ip_entry = tk.Entry(ip_frame, textvariable=self.ip_var, width=15)
        ip_entry.pack(side='left', padx=5)
        
        auto_ip_check = tk.Checkbutton(ip_frame, text='Auto-detect IP', variable=self.auto_ip_var,
                                      command=toggle_ip_entry, bg=self.settings['theme_color'])
        auto_ip_check.pack(side='left', padx=5)
        toggle_ip_entry()  # Initial state

        # Port
        port_frame = tk.Frame(server_frame, bg=self.settings['theme_color'])
        port_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(port_frame, text='Port:', bg=self.settings['theme_color']).pack(side='left', padx=5)
        self.port_var = tk.StringVar(value='5001')
        port_entry = tk.Entry(port_frame, textvariable=self.port_var, width=6)
        port_entry.pack(side='left', padx=5)

        # Server controls
        control_frame = tk.Frame(server_frame, bg=self.settings['theme_color'])
        control_frame.pack(fill='x', padx=5, pady=5)
        
        def start_server():
            try:
                port = int(self.port_var.get())
                host = '' if self.auto_ip_var.get() else self.ip_var.get()

                run_server(port=5001)

            except ValueError:
                messagebox.showerror("Error", "Invalid port number")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start server: {str(e)}")

        def stop_server():
            if hasattr(self, 'server'):
                messagebox.showinfo("Server Not stopped, please close the porgramm and try again", "TCP Server has been stopped")

        tk.Button(control_frame, text='Start Server', command=start_server,
                 bg='#4caf50', fg='white').pack(side='left', padx=5)
        tk.Button(control_frame, text='Stop Server', command=stop_server,
                 bg='#f44336', fg='white').pack(side='left', padx=5)

    def set_random_theme(self):
        random_color = random.choice(self.theme_colors)
        self.color_menu.set(random_color) # Update combobox
        self.settings['theme_color'] = random_color # Update settings
        save_settings(self.settings) # Save to file
        self.apply_theme_callback() # Apply to main app
        messagebox.showinfo('Theme', f'Random theme applied: {random_color}')

    def apply_theme_to_widgets(self):
        """Applies the current theme settings to all relevant widgets in the main application."""
        if self.app_state.settings.get('dark_mode', False):
            bg_color = '#23272e'
            fg_color = '#f0f0f0'
        else:
            bg_color = self.app_state.get_setting('theme_color', '#e3f2fd')
            fg_color = '#000000'
        
        # Configure ttk styles for themed widgets
        style = ttk.Style()
        style.theme_use('default') # Reset to default to avoid issues with other themes
        style.configure('TNotebook', background=bg_color)
        style.map('TNotebook.Tab', background=[('selected', bg_color)], foreground=[('selected', fg_color)])
        style.configure('TCombobox', fieldbackground=bg_color, background=bg_color, foreground=fg_color)
        style.map('TCombobox', fieldbackground=[('readonly', bg_color)])
        
        # Update background of the main window's content frame (assuming it's a Frame)
        # The root window (self.parent.master) itself does not have a 'bg' option, 
        # so we apply the background to its primary content frame if it exists.
        # Instead of iterating through children here, we'll let the recursive update_widget_colors handle it
        
        # Update all frames and widgets within the parent
        def update_widget_colors(widget):
            if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton, tk.Radiobutton, tk.Entry, tk.Listbox, tk.Text, tk.LabelFrame)):
                # These tk widgets support bg and fg
                try:
                    widget.configure(bg=bg_color, fg=fg_color)
                except tk.TclError:
                    pass
            elif isinstance(widget, (tk.Frame, ttk.Frame)):
                # tk.Frame and ttk.Frame support bg
                try:
                    widget.configure(bg=bg_color)
                except tk.TclError:
                    pass
            elif isinstance(widget, (ttk.Notebook, ttk.Combobox, ttk.Treeview, ttk.Scrollbar)):
                # ttk widgets are styled via ttk.Style, no direct bg/fg
                pass
            elif isinstance(widget, tk.Tk):
                # The root Tk window doesn't support bg directly
                pass
            
            # Recursively update children
            for child in widget.winfo_children():
                update_widget_colors(child)
        
        update_widget_colors(self.parent.master)
