from flask import request, jsonify

from models.models import Video
from utils.db_init import db
from utils.api_router import api


@api.route("/api/videos", methods=["GET"])
def get_videos():
    try:
        videos = Video.query.all()
        video_list = [video.to_dict() for video in videos]
        return jsonify({"data": video_list}), 200

    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 500


@api.route("/api/video/<int:video_id>", methods=["GET"])
def get_video(video_id):
    try:
        video = Video.query.filter(video_id=video_id)
        if video is None:
            return jsonify({"error": "Video not found"})

        return jsonify({"data": video.to_dict()}), 200

    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 500


@api.route("/api/create_video", methods=["POST"])
def create_video():
    try:
        data = request.get_json()
        new_video = Video(
            video_id=data["video_id"],
            title=data["title"],
            description=data["description"],
            url=data["url"],
            user_id=data["user_id"],
            categories=data["categories"],
        )

        db.session.add(new_video)
        db.session.commit()

        return jsonify({"message": "Video added"}), 200

    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 400


@api.route("/api/update_video/<int:video_id>", methods=["PUT"])
def update_video(video_id):

    video = Video.query.get(video_id)
    if video is None:
        return jsonify({"error": "Video not found"})

    data = request.get_json()

    video.title = data.get("title", video.title)
    video.description = data.get("description", video.description)
    video.url = data.get("url", video.url)
    video.views = data.get("views", video.views)

    db.session.commit()

    return jsonify(video.to_dict()), 200


@api.route("/api/delete_video/<int:video_id>", methods=["DELETE"])
def delete_video(video_id):
    video = Video.query.get(video_id)
    if video is None:
        return jsonify({"error": "Video not found"})

    db.session.delete(video)
    db.session.commit()
    return jsonify({"message": "Video deleted successfully"}), 204
