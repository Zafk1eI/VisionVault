from flask import request, jsonify

from models.models import Video, Comment, User
from utils.db_init import db
from utils.api_router import api

# get all comments for video
@api.route("/api/videos/comments/<int:video_id>", methods=["GET"])
def get_video_comments(video_id):
    video = Video.query.get(video_id)
    if video is None:
        return jsonify({"error": "Commented Video not found"}), 404

    comments = Comment.query.filter_by(video_id=video_id).all()
    return jsonify([comment.to_dict() for comment in comments]), 200


# get one comment for comment_id
@api.route("/api/comments/<int:comment_id>", methods=["GET"])
def get_comment(comment_id):
    comment = Comment.query.get(comment_id)
    
    if comment is None:
        return jsonify({"error": "Comment not found"}), 404

    return jsonify(comment.to_dict()), 200


@api.route("/api/videos//comments/<int:video_id>", methods=["POST"])
def add_comment_to_video(video_id):
    data = request.get_json()
    
    user_id = data.get("user_id")
    text = data.get("text")

    video = Video.query.get(video_id)
    user = User.query.get(user_id)
    if video is None or user is None:
        return jsonify({"error": "Video or user not found"}), 404


    comment = Comment(video_id=video_id, user_id=user_id, text=text)
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_dict()), 201


@api.route("/api/comments/<int:comment_id>", methods=["PUT"])
def update_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        return jsonify({"error": "Comment not found"}), 404

    data = request.get_json()
    comment.text = data.get("text", comment.text)

    db.session.commit()
    return jsonify(comment.to_dict()), 200


@api.route("/api/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        return jsonify({"error": "Comment not found"}), 404

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comment deleted successfully"}), 204