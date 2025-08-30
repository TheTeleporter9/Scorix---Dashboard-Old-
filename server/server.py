from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create scores directory if it doesn't exist
if not os.path.exists('scores'):
    os.makedirs('scores')

# Store current game state
current_game = {
    "gameNumber": "",
    "team1": {
        "name": "",
        "score": 0,
        "orange": 0,
        "purple": 0,
        "penalty": ""
    },
    "team2": {
        "name": "",
        "score": 0,
        "orange": 0,
        "purple": 0,
        "penalty": ""
    }
}

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000) 