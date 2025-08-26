from core.match_scheduler import set_match_comment, get_match_comment
from data.mongodb_client import collection as main_collection
from datetime import datetime

def set_match_comment_data(match_id, comment, schedule):
    """Set comment for a match and add to in-memory and MongoDB history"""
    set_match_comment(schedule, match_id, comment)
    # Add to in-memory history
    if 'comment_history' not in schedule['matches'][match_id]:
        schedule['matches'][match_id]['comment_history'] = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    schedule['matches'][match_id]['comment_history'].append({
        'comment': comment,
        'timestamp': timestamp
    })
    # Add to MongoDB
    add_comment_to_history(match_id, comment, timestamp)
    return True

def add_comment_to_history(match_id, old_comment, timestamp):
    """Add comment to match history"""
    comment_data = {
        'match_id': match_id,
        'comment': old_comment,
        'timestamp': timestamp
    }
    
    # Add to MongoDB collection
    main_collection.insert_one(comment_data)
    return True

def get_comment_history():
    """Get all comment history from MongoDB"""
    comments = list(main_collection.find({}, {'_id': 0}).sort('timestamp', -1))
    return comments

def get_team_comment_history(team):
    """Get comment history for a specific team"""
    comments = list(main_collection.find({'team': team}, {'_id': 0}).sort('timestamp', -1))
    return comments

def clear_comment_history():
    """Clear all comment history"""
    main_collection.delete_many({})
    return True

def delete_comment_from_history(comment_id):
    """Delete a specific comment from history"""
    main_collection.delete_one({'_id': comment_id})
    return True 