def publish_to_display(schedule, finals_data=None):
    """Publish the current state to the display collection"""
    from data.mongodb_client import display_collection
    doc = {
        'schedule': schedule,
        'finals': finals_data
    }
    display_collection.replace_one({}, doc, upsert=True)
