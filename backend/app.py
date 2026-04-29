from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, decode_token
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, join_room, emit
from flask import request
import os
import sys
from bson import ObjectId

from config import Config

# When this file is executed directly (`python app.py`), its module name is `__main__`.
# Routes import from `app`, so we alias `app` to the current module to avoid
# creating a second module instance with an uninitialized PyMongo extension.
sys.modules.setdefault("app", sys.modules[__name__])

mongo = PyMongo()
jwt = JWTManager()
bcrypt = Bcrypt()
socketio = SocketIO(cors_allowed_origins="*")
active_users = {}
sid_to_user = {}

def serialize(doc):
    """Convert a MongoDB document to a JSON-safe dict.

    - Renames ``_id`` to ``id`` (string).
    - Converts every remaining ``ObjectId`` value to ``str``.
    - Converts every ``datetime`` value to an ISO-8601 string.
    """
    import datetime as _dt

    if doc is None:
        return None

    out = {}
    for key, value in doc.items():
        if key == "_id":
            out["id"] = str(value)
        elif isinstance(value, ObjectId):
            out[key] = str(value)
        elif isinstance(value, (_dt.datetime, _dt.date)):
            out[key] = value.isoformat()
        elif isinstance(value, dict):
            out[key] = serialize(value)
        elif isinstance(value, list):
            out[key] = [
                serialize(v) if isinstance(v, dict)
                else str(v) if isinstance(v, ObjectId)
                else v.isoformat() if isinstance(v, (_dt.datetime, _dt.date))
                else v
                for v in value
            ]
        else:
            out[key] = value
    return out

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
    socketio.init_app(app, cors_allowed_origins="*")

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
    from routes.projects import projects_bp
    from routes.follow import follow_bp
    from routes.search import search_bp
    from routes.earnings import earnings_bp

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
    app.register_blueprint(projects_bp)
    app.register_blueprint(follow_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(earnings_bp)

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'FreelanceHub API is running'}

    from routes.socket import register_socket_handlers
    register_socket_handlers()
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
