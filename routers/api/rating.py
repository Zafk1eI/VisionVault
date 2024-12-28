from flask import request, jsonify

from models.models import User, Video, Rating
from utils.db_init import db
from utils.api_router import api


@api.route("/api/videos/rate/<int:video_id>", methods=["POST"])
def rate_video(video_id):
    data = request.get_json()

    user_id = data.get("user_id")
    rating_value = data.get(
        "rating"
    )  # rating_value может быть 1 (лайк), -1 (дизлайк) или другое

    video = Video.query.get(video_id)
    user = User.query.get(user_id)

    if video is None or user is None:
        return jsonify({"error": "Video or user not found"}), 404

    existing_rating = Rating.query.filter_by(video_id=video_id, user_id=user_id).first()
    if existing_rating:
        existing_rating.rating = rating_value
    else:
        new_rating = Rating(video_id=video_id, user_id=user_id, rating=rating_value)
        db.session.add(new_rating)

    db.session.commit()
    return jsonify({"message": "Rating updated successfully"}), 201


@api.route("/api/videos/<int:video_id>/rate", methods=["DELETE"])
def delete_rating(video_id):
    data = request.get_json()
    user_id = data.get("user_id")

    video = Video.query.get(video_id)
    user = User.query.get(user_id)
    if video is None or user is None:
        return jsonify({"error": "Video or user not found"}), 404

    existing_rating = Rating.query.filter_by(video_id=video_id, user_id=user_id).first()
    if existing_rating:
        db.session.delete(existing_rating)
        db.session.commit()
        return jsonify({"message": "Rating deleted successfully"}), 204
    else:
        return jsonify({"error": "Rating not found"}), 404
