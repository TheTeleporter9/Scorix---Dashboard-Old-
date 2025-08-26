from data.mongodb_client import get_all_games, collection as main_collection
from core.tournament_logic import get_next_game, get_leaderboard
from utils.excel_exporter import export_games_to_excel
from datetime import datetime
import json

def refresh_tournament_data():
    """Refresh all data from MongoDB and return updated data"""
    games = get_all_games()
    next_game = get_next_game(games)
    leaderboard = get_leaderboard(games)
    
    return {
        'games': games,
        'next_game': next_game,
        'leaderboard': leaderboard
    }

def export_excel():
    """Export games data to Excel"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'tournament_scores_{timestamp}.xlsx'
    export_games_to_excel(filename)
    return filename

def export_schedule_csv(schedule):
    """Export schedule to CSV format"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'schedule_{timestamp}.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvfile.write('Match,Team 1,Team 2,Status,Referee,Score 1,Score 2,Penalty 1,Penalty 2,Comment\n')
        
        for i, match in enumerate(schedule['matches'], 1):
            team1 = match.get('team1', '')
            team2 = match.get('team2', '')
            status = match.get('status', 'Not Started')
            referee = match.get('referee', '')
            score1 = match.get('score1', '')
            score2 = match.get('score2', '')
            penalty1 = match.get('penalty1', '')
            penalty2 = match.get('penalty2', '')
            comment = match.get('comment', '').replace('"', '""')  # Escape quotes
            
            csvfile.write(f'{i},"{team1}","{team2}","{status}","{referee}","{score1}","{score2}","{penalty1}","{penalty2}","{comment}"\n')
    
    return filename 