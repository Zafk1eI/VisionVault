from flask import request, jsonify
from models.models import User, Subscription
from utils.db_init import db
from utils.api_router import api


@api.route("/api/users/subscribe/<int:subscriber_id>", methods=["POST"])
def subscribe(subscriber_id):
    data = request.get_json()

    channel_id = data.get("channel_id")
    subscriber = User.query.get(subscriber_id)
    channel = User.query.get(channel_id)

    if subscriber is None or channel is None:
        jsonify({"error": "Subscriber or channel not found"}), 404

    existing_subscription = Subscription.query.filter_by(
        subscriber_id=subscriber_id, channel_id=channel_id
    ).first()
    if existing_subscription:
        return jsonify({"error": "Already subscribed to this channel"}), 400

    new_subscription = Subscription(subscriber_id=subscriber_id, channel_id=channel_id)
    db.session.add(new_subscription)
    db.session.commit()

    return jsonify({"message": "Successfully subscribed to channel"}), 201


@api.route("/api/users/<int:subscriber_id>/unsubscribe", methods=["DELETE"])
def unsubscribe(subscriber_id):
    data = request.get_json()
    channel_id = data.get("channel_id")

    subscriber = User.query.get(subscriber_id)
    channel = User.query.get(channel_id)
    if subscriber is None or channel is None:
        jsonify({"error": "Subscriber or channel not found"}), 404

    existing_subscription = Subscription.query.filter_by(
        subscriber_id=subscriber_id, channel_id=channel_id
    ).first()
    if existing_subscription:
        db.session.delete(existing_subscription)
        db.session.commit()
        return jsonify({"message": "Successfully unsubscribed from channel"}), 204
    else:
        return jsonify({"error": "Subscription not found"}), 404


@api.route("/api/users/<int:subscriber_id>/subscriptions", methods=["GET"])
def get_subscriptions(subscriber_id):
    subscriber = User.query.get(subscriber_id)
    if subscriber is None:
        jsonify({"error": "Subscriber not found"}), 404

    subscriptions = Subscription.query.filter_by(subscriber_id=subscriber_id).all()
    channels = [{"channel_id": sub.channel_id} for sub in subscriptions]

    return jsonify(channels), 200
