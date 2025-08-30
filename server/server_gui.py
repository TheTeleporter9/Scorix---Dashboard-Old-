import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from server import app, socketio
import sys
import queue
from datetime import datetime
import json
import os

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WRO Score Server")
        self.root.geometry("800x600")
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Server status frame
        self.status_frame = ttk.Frame(root)
        self.status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        self.status_label = ttk.Label(self.status_frame, text="Server Status: Stopped")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(self.status_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        # Log frame
        self.log_frame = ttk.Frame(root)
        self.log_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD)
        self.log_display.pack(fill=tk.BOTH, expand=True)
        
        # Connected clients frame
        self.clients_frame = ttk.LabelFrame(root, text="Connected Clients")
        self.clients_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.clients_label = ttk.Label(self.clients_frame, text="Connected: 0")
        self.clients_label.pack(pady=5)
        
        # Initialize variables
        self.server_running = False
        self.server_thread = None
        self.connected_clients = 0
        self.log_queue = queue.Queue()
        
        # Create scores directory if it doesn't exist
        if not os.path.exists('scores'):
            os.makedirs('scores')

        # Add table scores tracking
        self.table_scores = {
            '1': {'team1': 0, 'team2': 0},
            '2': {'team1': 0, 'team2': 0}
        }

        # Start checking for new log messages
        self.root.after(100, self.check_log_queue)

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def check_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.log_display.insert(tk.END, message)
            self.log_display.see(tk.END)
        self.root.after(100, self.check_log_queue)

    def start_server(self):
        if not self.server_running:
            self.server_running = True
            self.start_button.config(text="Stop Server")
            self.status_label.config(text="Server Status: Running")
            self.log("Server starting...")
            
            # Override socketio handlers to capture events
            @socketio.on('connect')
            def handle_connect():
                self.connected_clients += 1
                self.clients_label.config(text=f"Connected: {self.connected_clients}")
                self.log("Client connected")
            
            @socketio.on('disconnect')
            def handle_disconnect():
                self.connected_clients -= 1
                self.clients_label.config(text=f"Connected: {self.connected_clients}")
                self.log("Client disconnected")
            
            @socketio.on('saveGame')
            def handle_save_game(game_data):
                try:
                    # Create filename with timestamp and game number
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    game_number = game_data.get('gameNumber', 'unknown')
                    filename = f"scores/game_{game_number}_{timestamp}.json"
                    
                    # Save game data to JSON file
                    with open(filename, 'w') as f:
                        json.dump(game_data, f, indent=4)
                    
                    self.log(f"Game {game_number} saved successfully to {filename}")
                    socketio.emit('savingComplete', {
                        'status': 'success',
                        'message': 'Game saved successfully!'
                    })
                except Exception as e:
                    error_msg = f"Error saving game: {str(e)}"
                    self.log(error_msg)
                    socketio.emit('savingComplete', {
                        'status': 'error',
                        'message': error_msg
                    })
            
            @socketio.on('updateScore')
            def handle_score_update(data):
                table = data.get('table', '1')  # Default to table 1 if not specified
                scores = data.get('scores', {'team1': 0, 'team2': 0})
                self.table_scores[table] = scores
                self.log(f"Score update - Table {table} - Team 1: {scores['team1']}, Team 2: {scores['team2']}")
                
                # Broadcast the update to all displays
                socketio.emit('scoreUpdate', {
                    'table': table,
                    'scores': scores
                })

            @socketio.on('requestTableScore')
            def handle_score_request(data):
                table = str(data.get('table', '1'))
                if table in self.table_scores:
                    socketio.emit('scoreUpdate', {
                        'table': table,
                        'scores': self.table_scores[table]
                    })
            
            @socketio.on('requestLatestGame')
            def handle_latest_game_request(data):
                try:
                    table = data.get('table', '1')
                    scores_dir = 'scores'
                    
                    # Get list of JSON files and sort by timestamp (newest first)
                    json_files = [f for f in os.listdir(scores_dir) if f.endswith('.json')]
                    json_files.sort(reverse=True)
                    
                    if json_files:
                        # Read the latest file
                        with open(os.path.join(scores_dir, json_files[0]), 'r') as f:
                            latest_game = json.load(f)
                        
                        self.log(f"Sending latest game data from {json_files[0]}")
                        socketio.emit('latestGameData', {
                            'status': 'success',
                            'gameData': latest_game
                        })
                    else:
                        socketio.emit('latestGameData', {
                            'status': 'error',
                            'message': 'No saved games found'
                        })
                except Exception as e:
                    error_msg = f"Error reading latest game data: {str(e)}"
                    self.log(error_msg)
                    socketio.emit('latestGameData', {
                        'status': 'error',
                        'message': error_msg
                    })

            # Start server in a separate thread
            self.server_thread = threading.Thread(
                target=lambda: socketio.run(app, host='0.0.0.0', port=5000, debug=False)
            )
            self.server_thread.daemon = True
            self.server_thread.start()
        else:
            self.stop_server()

    def stop_server(self):
        if self.server_running:
            self.server_running = False
            self.start_button.config(text="Start Server")
            self.status_label.config(text="Server Status: Stopped")
            self.log("Server stopped")
            # Implement proper server shutdown here

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ServerGUI(root)
    gui.run() 