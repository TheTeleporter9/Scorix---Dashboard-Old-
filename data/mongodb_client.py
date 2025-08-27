# server.py
import json
import os
from pymongo import MongoClient
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# ---------------- MongoDB Settings ----------------
MONGO_URI = 'mongodb+srv://TheTeleporter9:JTMdX9HFCllYRJDX@wro-scoring.n0khn.mongodb.net/?retryWrites=true&w=majority'
DB_NAME = 'Wro-scoring'
COLLECTION_NAME = 'gamescores'
DISPLAY_COLLECTION = 'competition_display'
SCHEDULE_FILE = 'schedule.json'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
display_collection = db[DISPLAY_COLLECTION]

# ---------------- FastAPI Setup ----------------
app = FastAPI()

# Enable CORS for your Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your Flutter app origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for latest POSTed data
latest_data = {}

# ---------------- Helper Functions ----------------
def get_all_games():
    return list(collection.find())

def get_ranking_and_current_game():
    games = list(collection.find())
    scores = {}
    for g in games:
        t1 = g.get('Team1', {})
        t2 = g.get('Team2', {})
        for t in [t1, t2]:
            name = t.get('Name')
            if name:
                scores[name] = scores.get(name, 0) + t.get('Score', 0)
    ranking = sorted(scores.items(), key=lambda x: x[1])  # least points = top
    current_game = None
    for g in sorted(games, key=lambda x: x.get('timestamp', ''), reverse=True):
        if g.get('status', '').lower() == 'in progress' or not g.get('status'):
            current_game = g
            break
    return ranking, current_game

def get_next_up_match_from_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return None
    with open(SCHEDULE_FILE, 'r') as f:
        schedule = json.load(f)
    for match in schedule.get('matches', []):
        if match.get('next_up', False):
            return match
    return None

def sync_scores_to_schedule():
    schedule = None
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            schedule = json.load(f)
    if not schedule:
        return
    games = get_all_games()
    for match in schedule.get('matches', []):
        for game in games:
            t1 = game.get('Team1', {})
            t2 = game.get('Team2', {})
            if (match.get('team1') == t1.get('Name', '') and match.get('team2') == t2.get('Name', '')) or \
               (match.get('team1') == t2.get('Name', '') and match.get('team2') == t1.get('Name', '')):
                if match.get('team1') == t1.get('Name', ''):
                    match['score1'] = t1.get('Score', 0)
                    match['score2'] = t2.get('Score', 0)
                else:
                    match['score1'] = t2.get('Score', 0)
                    match['score2'] = t1.get('Score', 0)
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f, indent=2)

def get_display_payload():
    next_up_match = get_next_up_match_from_schedule()
    ranking, _ = get_ranking_and_current_game()
    team_to_rank = {team: idx+1 for idx, (team, _) in enumerate(sorted(ranking, key=lambda x: x[1]))}

    if next_up_match:
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                schedule = json.load(f)
            match_number = str(schedule['matches'].index(next_up_match) + 1)
        except Exception:
            match_number = ''
        teamAName = next_up_match.get('team1', '')
        teamBName = next_up_match.get('team2', '')
        teamARank = team_to_rank.get(teamAName, 0)
        teamBRank = team_to_rank.get(teamBName, 0)
    else:
        match_number = ''
        teamAName = ''
        teamARank = 0
        teamBName = ''
        teamBRank = 0

    return {
        'matchNumber': match_number,
        'tableNumber': 'Table 1',
        'teamAName': teamAName,
        'teamARank': teamARank,
        'teamBName': teamBName,
        'teamBRank': teamBRank
    }

# ---------------- FastAPI Endpoints ----------------
@app.post("/update")
async def update_data(request: Request):
    global latest_data
    latest_data = await request.json()
    print("📥 Received update:", latest_data)

    # Save to MongoDB
    collection.insert_one(latest_data)

    # Sync scores to schedule.json
    sync_scores_to_schedule()

    # Return display payload
    payload = get_display_payload()
    return payload

@app.get("/latest")
def get_latest_data():
    return latest_data

@app.get("/display")
def get_display_data():
    return get_display_payload()

# ---------------- Run Server ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
