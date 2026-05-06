from app import create_app, mongo
from pymongo import ASCENDING, DESCENDING, TEXT

def setup_indexes():
    app = create_app()
    with app.app_context():
        print("Creating indexes...")
        # Text indexes
        mongo.db.offers.create_index([("title", TEXT), ("description", TEXT)])
        mongo.db.services.create_index([("title", TEXT), ("description", TEXT)])
        
        # Performance indexes
        mongo.db.offers.create_index([("status", ASCENDING)])
        mongo.db.proposals.create_index([("offer_id", ASCENDING)])
        mongo.db.messages.create_index([("conversation_id", ASCENDING)])
        mongo.db.notifications.create_index([("user_id", ASCENDING), ("is_read", ASCENDING)])
        mongo.db.users.create_index([("role", ASCENDING), ("status", ASCENDING)])
        mongo.db.users.create_index([("interests", ASCENDING)])
        mongo.db.users.create_index([("username", ASCENDING)], unique=True, sparse=True)
        mongo.db.offers.create_index([("status", ASCENDING), ("category", ASCENDING), ("created_at", DESCENDING)])
        mongo.db.offers.create_index([("skills", ASCENDING)])
        mongo.db.freelancer_profiles.create_index([("user_id", ASCENDING)])
        mongo.db.freelancer_profiles.create_index([("skills", ASCENDING)])
        mongo.db.freelancer_profiles.create_index([("availability_status", ASCENDING)])
        mongo.db.reviews.create_index([("target_id", ASCENDING)])
        mongo.db.recommendation_interactions.create_index([("user_id", ASCENDING), ("item_type", ASCENDING), ("action", ASCENDING), ("created_at", DESCENDING)])
        mongo.db.recommendation_feedback.create_index([("user_id", ASCENDING), ("item_type", ASCENDING), ("item_id", ASCENDING)])
        
        print("Indexes created successfully.")

if __name__ == "__main__":
    setup_indexes()
