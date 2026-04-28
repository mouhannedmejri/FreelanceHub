from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
import os
from bson import ObjectId

from config import Config

mongo = PyMongo()
jwt = JWTManager()
bcrypt = Bcrypt()

def serialize(doc):
    if doc is None: return None
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

def serialize_list(docs):
    return [serialize(d) for d in docs]

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Check if user is banned
    @jwt.token_in_blocklist_loader
    def check_if_banned(jwt_header, jwt_data):
        user_id = jwt_data["sub"]
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        return user and user.get("status") == "banned"

    # Register blueprints
    from routes.auth import auth_bp
    from routes.home import home_bp
    from routes.notifications import notifications_bp
    from routes.services import services_bp
    from routes.users import users_bp
    from routes.offers import offers_bp
    from routes.conversations import conversations_bp
    from routes.store import store_bp
    from routes.proposals import proposals_bp
    from routes.reviews import reviews_bp
    from routes.admin import admin_bp
    from routes.client import client_bp
    from routes.freelancer import freelancer_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(proposals_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(freelancer_bp)

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'FreelanceHub API is running'}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
