from flask import request, jsonify
from models.models import Video, Category, VideoCategories
from utils.db_init import db
from utils.api_router import api


@api.route("/api/videos/<int:video_id>/categories", methods=["POST"])
def add_categories_to_video(video_id):
    video = Video.query.get(video_id)
    if video is None:
        jsonify({'error': "Video not found"}), 404

    data = request.get_json()
    category_ids = data.get("category_ids")

    if not category_ids or not isinstance(category_ids, list):
        return jsonify({"error": "Category IDs must be provided as a list"}), 400

    categories = Category.query.filter(Category.category_id.in_(category_ids)).all()
    if len(categories) != len(category_ids):
        return jsonify({"error": "One or more categories not found"}), 404

    for category in categories:
        existing_association = VideoCategories.query.filter_by(video_id=video_id, category_id=category.category_id).first()
        if not existing_association:
            new_association = VideoCategories(video_id=video_id, category_id=category.category_id)
            db.session.add(new_association)

    db.session.commit()
    return jsonify({"message": "Categories added to video successfully"}), 201


@api.route("/api/videos/<int:video_id>/categories/<int:category_id>", methods=["DELETE"])
def delete_category_from_video(video_id, category_id):
    association = VideoCategories.query.filter_by(video_id=video_id, category_id=category_id).first()
    if association is None:
        return jsonify({"error": "Association not found"}), 404

    db.session.delete(association)
    db.session.commit()
    return jsonify({"message": "Category removed from video successfully"}), 204


@api.route("/api/videos/<int:video_id>/categories", methods=["GET"])
def get_categories_for_video(video_id):
    video = Video.query.get(video_id)
    if video is None:
        jsonify({'error': "Video not found"}), 404

    categories = video.categories 
    category_list = [{"category_id": cat.category_id, "category_name": cat.category_name} for cat in categories]
    return jsonify(category_list), 200


# 4. Получить список видео для категории
@api.route("/api/categories/<int:category_id>/videos", methods=["GET"])
def get_videos_for_category(category_id):
    category = Category.query.get(category_id)
    if category is None:
        jsonify({'error': "Category not found"}), 404

    videos = category.videos
    video_list = [{"video_id": video.video_id, "title": video.title, "description": video.description, "url": video.url} for video in videos]
    return jsonify(video_list), 200
