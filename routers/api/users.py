from flask import request, jsonify

from models.models import User
from utils.db_init import db
from utils.api_router import api


@api.route("/api/users", methods=["GET"])
def get_users():
    try:
        users = User.query.all()
        user_list = [user.to_dict() for user in users]
        return jsonify({"data": user_list}), 200

    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 500


@api.route("/api/user/<int:id>", methods=["GET"])
def get_one_user(id):
    try:
        user = User.query.filter(user_id=id).first()
        if user is None:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"data": user.to_dict()}), 200

    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 500


@api.route("/api/create_user", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        new_user = User(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            photo_url=data["photo_url"],
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User added"}), 200
    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 400


@api.route("/api/update_user/<int:id>", methods=["PUT"])
def get_user(id):
    try:
        user_fields = ["user_id", "username", "email", "photo_url"]
        user = User.query.filter(user_id=id).first()
        if user is None:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()

        for field in user_fields:
            if field in data.keys():
                setattr(user, field, data[field])

        db.session.commit()

        return jsonify({"message": "user updated"}), 201

    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 500


@api.route("/api/delete_user/<int:id>", methods=["DELETE"])
def delete_user(id):
    try:
        user = User.query.filter(user_id=id).first()
        if user is None:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "user deleted"}), 200
    except Exception as exc:
        return jsonify({"error": f"{exc}"}), 400
