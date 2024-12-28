from flask import Blueprint, session, jsonify, render_template, request
from models.models import Video, User, Rating, History, Subscription
from flask import render_template
from utils.socketio import socketio
from utils.db_init import db
from flask_socketio import emit, join_room, leave_room

websoket = Blueprint("websocket", __name__)

@websoket.route("/room/<string:video_id>/<string:room_id>")
def room(video_id, room_id):
    user_id = session.get("user_id")
    
    video = Video.query.filter(Video.video_id == video_id).first()

    if not video:
        return jsonify({"error": "404"}), 404

    user_rating = None
    user = None

    if user_id:
        user = User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({'error':"User not found"}), 404
        
        existing_history = History.query.filter_by(
            video_id=video_id, user_id=user_id
        ).first()

        if not existing_history:
            history_entry = History(
                video_id=video_id,
                user_id=user_id,
                visibility=True if user.retain_history is True else False,
            )
            db.session.add(history_entry)
            db.session.commit()

            video.views += 1
            db.session.commit()
        else:
            if user.retain_history is True:
                existing_history.visibility = True
                db.session.commit()

        channel_id = video.user_id
        subscribe = Subscription.query.filter(
            Subscription.channel_id == channel_id, Subscription.subscriber_id == user_id
        ).first()

        rating = Rating.query.filter_by(video_id=video_id, user_id=user_id).first()
        if rating:
            user_rating = rating.rating

        video.is_subscribed = bool(subscribe)
        
    else:
        video.is_subscribed = False

    return render_template("websocket_room.html", 
                        video=video, 
                        user_rating=user_rating,
                        user=user,
                        room_id=room_id,
                        )


@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")


@socketio.on('join_room')
def on_join(data):
    try:
        room = data.get('room')
        if room:
            join_room(room)
            emit('user_joined', {'user': request.sid}, room=room)
    except Exception as e:
        print(f"Error in join_room: {e}")


@socketio.on('leave_room')
def on_leave(data):
    try:
        room = data.get('room')
        if room:
            leave_room(room)
            emit('user_left', {'user': request.sid}, room=room)
    except Exception as e:
        print(f"Error in leave_room: {e}")


@socketio.on('video_action')
def handle_video_action(data):
    try:
        room = data.get('room')
        if room:
            emit('sync_video', {
                'action': data.get('action'),
                'current_time': data.get('current_time')
            }, room=room, include_sender=False)
    except Exception as e:
        print(f"Error in video_action: {e}")
