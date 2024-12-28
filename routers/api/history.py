from datetime import datetime, timezone

from flask import request, jsonify

from models.models import User, Video, History
from utils.db_init import db
from utils.api_router import api


@api.route("/api/users/history/<int:user_id>", methods=["GET"])
def get_user_history(user_id):

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    history_records = History.query.filter_by(user_id=user_id).all()
    history_list = [
        {
            "video_id": record.video_id,
            "viewed_at": record.viewed_at,
        }
        for record in history_records
    ]

    return jsonify(history_list), 200


@api.route("/api/videos/<int:video_id>/history", methods=["POST"])
def add_to_history(video_id):
    data = request.get_json()
    user_id = data.get("user_id")

    video = Video.query.get(video_id)
    user = User.query.get(user_id)
    if video is None or user is None:
        return jsonify({"error": "Video or user not found"}), 404

    existing_history = History.query.filter_by(
        video_id=video_id, user_id=user_id
    ).first()
    if existing_history:
        existing_history.viewed_at = datetime.now(timezone.utc)
    else:
        new_history = History(video_id=video_id, user_id=user_id)
        db.session.add(new_history)

    db.session.commit()
    return jsonify({"message": "History updated successfully"}), 201


@api.route("/api/history/<int:history_id>", methods=["DELETE"])
def delete_history_record(history_id):
    history_record = History.query.get(history_id)
    if history_record is None:
        return jsonify({"error": "History record not found"}), 404

    db.session.delete(history_record)
    db.session.commit()
    return jsonify({"message": "History record deleted successfully"}), 204
