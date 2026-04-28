from flask import request
from flask_jwt_extended import decode_token
from bson import ObjectId
from app import socketio, mongo, active_users, sid_to_user
from flask_socketio import join_room, emit

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
