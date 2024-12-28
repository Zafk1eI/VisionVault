from flask import request, jsonify

from models.models import Video, Category, VideoCategories
from utils.db_init import db
from utils.api_router import api


@api.route("/api/categories", methods=["POST"])
def add_category():
    data = request.get_json()
    category_name = data.get("category_name")

    if not category_name:
        return jsonify({"error": "Category name is required"}), 400

    existing_category = Category.query.filter_by(category_name=category_name).first()
    if existing_category:
        return jsonify({"error": "Category already exists"}), 400

    new_category = Category(category_name=category_name)
    db.session.add(new_category)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Category added successfully",
                "category_id": new_category.category_id,
            }
        ),
        201,
    )


@api.route("/api/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    category = Category.query.get(category_id)
    if category is None:
        return jsonify({"error": "Category not found"}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 204


@api.route("/api/categories/<int:category_id>/videos", methods=["GET"])
def get_videos_by_category(category_id):
    category = Category.query.get(category_id)
    if category is None:
        jsonify({"error": "Category not found"}), 404
    videos = category.videos
    video_list = [video.to_dict() for video in videos]
    return jsonify(video_list), 200
