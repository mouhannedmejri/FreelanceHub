from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT

def setup_indexes():
    client = MongoClient("mongodb://localhost:27017/") # Adjust to config if needed
    db = client.freelancehub # Adjust DB name if different. In app.py it uses flask_pymongo.
    
    # Text indexes
    db.offers.create_index([("title", TEXT), ("description", TEXT)])
    db.services.create_index([("title", TEXT), ("description", TEXT)])
    
    # Performance indexes
    db.offers.create_index([("status", ASCENDING)])
    db.proposals.create_index([("offer_id", ASCENDING)])
    db.messages.create_index([("conversation_id", ASCENDING)])
    db.notifications.create_index([("user_id", ASCENDING), ("is_read", ASCENDING)])
    db.users.create_index([("role", ASCENDING), ("status", ASCENDING)])
    db.users.create_index([("interests", ASCENDING)])
    db.users.create_index([("username", ASCENDING)], unique=True, sparse=True)
    db.offers.create_index([("status", ASCENDING), ("category", ASCENDING), ("created_at", DESCENDING)])
    db.offers.create_index([("skills", ASCENDING)])
    db.freelancer_profiles.create_index([("user_id", ASCENDING)])
    db.freelancer_profiles.create_index([("skills", ASCENDING)])
    db.freelancer_profiles.create_index([("availability_status", ASCENDING)])
    db.reviews.create_index([("target_id", ASCENDING)])
    db.recommendation_interactions.create_index([("user_id", ASCENDING), ("item_type", ASCENDING), ("action", ASCENDING), ("created_at", DESCENDING)])
    db.recommendation_feedback.create_index([("user_id", ASCENDING), ("item_type", ASCENDING), ("item_id", ASCENDING)])

    print("Indexes created successfully.")

if __name__ == "__main__":
    setup_indexes()
