from app import create_app, mongo
from pymongo import ASCENDING, TEXT

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
        
        print("Indexes created successfully.")

if __name__ == "__main__":
    setup_indexes()
