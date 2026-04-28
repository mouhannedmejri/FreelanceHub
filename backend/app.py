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

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'FreelanceHub API is running'}

    register_socket_handlers()
    return app

def register_socket_handlers():
    @socketio.on("connect")
    def on_connect(auth):
        token = None
        if isinstance(auth, dict):
            token = auth.get("token")
        if not token:
            return False

        try:
            decoded = decode_token(token)
            user_id = decoded.get("sub")
            if not user_id:
                raise ValueError("Missing subject")
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if not user or user.get("status") == "banned":
                raise ValueError("Unauthorized")
        except Exception as exc:
            raise ConnectionRefusedError(f"Invalid token: {exc}") from exc

        active_users[user_id] = active_users.get(user_id, 0) + 1
        sid_to_user[request.sid] = user_id
        join_room(f"user:{user_id}")

        conversations = mongo.db.conversations.find({"participant_ids": user_id})
        for conv in conversations:
            conv_id = str(conv["_id"])
            join_room(f"conversation:{conv_id}")
            emit(
                "user:online",
                {"user_id": user_id, "online": True},
                room=f"conversation:{conv_id}",
            )
            for participant_id in conv.get("participant_ids", []):
                if participant_id in active_users:
                    emit(
                        "user:online",
                        {"user_id": participant_id, "online": True},
                        room=request.sid,
                    )

    @socketio.on("disconnect")
    def on_disconnect():
        user_id = sid_to_user.pop(request.sid, None)

        if not user_id:
            return

        active_users[user_id] = max(active_users.get(user_id, 1) - 1, 0)
        if active_users[user_id] > 0:
            return

        del active_users[user_id]
        conversations = mongo.db.conversations.find({"participant_ids": user_id})
        for conv in conversations:
            conv_id = str(conv["_id"])
            emit(
                "user:online",
                {"user_id": user_id, "online": False},
                room=f"conversation:{conv_id}",
            )

    @socketio.on("user:typing")
    def on_user_typing(data):
        if not isinstance(data, dict):
            return
        conversation_id = data.get("conversation_id")
        user_id = data.get("user_id")
        is_typing = bool(data.get("is_typing", False))
        if not conversation_id or not user_id:
            return
        emit(
            "user:typing",
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "is_typing": is_typing,
            },
            room=f"conversation:{conversation_id}",
            include_self=False,
        )

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
