from flask import (
    Blueprint,
    flash,
    render_template,
    session,
    redirect,
    send_file,
    abort,
    url_for,
    request,
    jsonify,
    send_from_directory,
)

from io import BytesIO
import os
from uuid import uuid4
from ast import literal_eval
from datetime import date, timedelta, datetime
from sqlalchemy import desc
import json

import locale

from models.models import (
    Category,
    Video,
    History,
    Subscription,
    User,
    Rating,
    Comment,
    VideoCategories,
)
from utils.db_init import db
from utils.jinja_filters import time_since_upload, format_views
from utils.file_to_hls import convert_video_to_hls


router = Blueprint("routers", __name__)

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


def update_like_dislike_count(video_id):
    likes_count = Rating.query.filter_by(video_id=video_id, rating=True).count()
    dislikes_count = Rating.query.filter_by(video_id=video_id, rating=False).count()

    video = Video.query.get(video_id)
    video.likes = likes_count
    video.dislikes = dislikes_count
    db.session.commit()


@router.route("/", methods=["GET"])
def index():
    user_id = session.get("user_id")
    user = User.query.filter(User.user_id == user_id).first()
    return render_template("index.html", user=user)


@router.route("/get_thumbnail/<video_id>/thumbnail.jpg")
def video_thumbnail(video_id):
    thumbnail_directory = os.path.join("videos", video_id)
    return send_from_directory(thumbnail_directory, "thumbnail.jpg")


@router.route("/get_video_hls/<path:video_id>/<path:filename>")
def get_file_for_player(video_id, filename):

    path_to_folder = os.path.join("videos", video_id, filename)
    print(path_to_folder)

    if not os.path.exists(path_to_folder):
        print("Путь к файлу не найден")
        abort(400, description="Video folder does not exist")

    return send_file(path_to_folder)


@router.post("/subscribe/<int:channel_id>")
def subscribe(channel_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    channel = Subscription.query.filter(
        Subscription.channel_id == channel_id, Subscription.subscriber_id == user_id
    ).first()
    if channel:
        return jsonify({"success": False, "error": "Already subscribed"}), 400

    try:
        new_subscription = Subscription(subscriber_id=user_id, channel_id=channel_id)
        db.session.add(new_subscription)
        db.session.commit()
        return jsonify({"success": True, "msg": "subscribed"}), 200
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to subscribe"}), 500


@router.post("/unsubscribe/<int:channel_id>")
def unsubscribe(channel_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        subscription = Subscription.query.filter(
            Subscription.channel_id == channel_id, Subscription.subscriber_id == user_id
        ).first()
        if subscription:
            db.session.delete(subscription)
            db.session.commit()
            return jsonify({"success": True, "msg": "unsubscribed"}), 200
        else:
            return jsonify({"success": False, "error": "Subscription not found"}), 404
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to unsubscribe"}), 500


@router.route("/like/<string:video_id>", methods=["POST"])
def like_video(video_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    video = Video.query.filter_by(video_id=video_id).first()
    if not video:
        return jsonify({"success": False, "error": "Video not found"}), 404

    existing_rating = Rating.query.filter_by(video_id=video_id, user_id=user_id).first()

    if existing_rating:
        if existing_rating.rating:
            db.session.delete(existing_rating)
            video.likes -= 1
            action = "removed"
        else:
            existing_rating.rating = True
            video.likes += 1
            video.dislikes -= 1
            action = "liked"
    else:
        new_rating = Rating(video_id=video_id, user_id=user_id, rating=True)
        db.session.add(new_rating)
        video.likes += 1
        action = "liked"

    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "action": action,
                "likes": video.likes,
                "dislikes": video.dislikes,
            }
        ),
        200,
    )


@router.route("/dislike/<string:video_id>", methods=["POST"])
def dislike_video(video_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    video = Video.query.filter_by(video_id=video_id).first()
    if not video:
        return jsonify({"success": False, "error": "Video not found"}), 404

    existing_rating = Rating.query.filter_by(video_id=video_id, user_id=user_id).first()

    if existing_rating:
        if not existing_rating.rating:
            db.session.delete(existing_rating)
            video.dislikes -= 1
            action = "removed"
        else:
            existing_rating.rating = False
            video.likes -= 1
            video.dislikes += 1
            action = "disliked"
    else:
        new_rating = Rating(video_id=video_id, user_id=user_id, rating=False)
        db.session.add(new_rating)
        video.dislikes += 1
        action = "disliked"

    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "action": action,
                "likes": video.likes,
                "dislikes": video.dislikes,
            }
        ),
        200,
    )


@router.post("/post_comment/<string:video_id>")
def post_comment(video_id):
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    try:
        comment_text = request.form.get("comment")

        if not comment_text:
            return jsonify({"success": False, "error": "Comment text is required"}), 400

        comment = Comment(
            text=comment_text,
            user_id=user_id,
            video_id=video_id,
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({"success": True, "msg": "comment added"}), 200
    except Exception as e:
        print(f"Error while adding comment: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": "Server error"}), 500


# TODO: 404 page
@router.route("/watch/<string:video_id>")
def player(video_id):
    user_id = session.get("user_id")

    video = Video.query.filter(Video.video_id == video_id).first()

    if not video:
        return jsonify({"error": "404"}), 404

    user_rating = None
    user = None

    if user_id:
        user = User.query.filter_by(user_id=user_id).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

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

    room_id = str(uuid4())
    return render_template(
        "player.html",
        video=video,
        user_rating=user_rating,
        user=user,
        room_id=room_id,
    )


@router.route("/history")
def get_history():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("auth.login"))

    user = User.query.filter(User.user_id == user_id).first()

    if not user:
        return redirect(url_for("auth.login"))

    user_history = History.query.filter(
        History.user_id == user_id, History.visibility == True
    ).limit(100)

    grouped_history = {}
    today = date.today()

    for history in user_history:
        viewed_date = history.viewed_at.date()

        if viewed_date == today:
            key = "Сегодня"
        elif viewed_date == today - timedelta(days=1):
            key = "Вчера"
        else:
            key = viewed_date.strftime("%d %B %Y")

        if key not in grouped_history:
            grouped_history[key] = []

        if history.video:
            grouped_history[key].append(history)
    
    for key, videos in grouped_history.items():
        print(f"{key}: {[video.video_id if video.video else None for video in videos]}")

    
    return render_template("history.html", grouped_history=grouped_history, user=user)


@router.route("/report")
def report():
    return render_template("report.html")


@router.route("/channel")
def channel():
    return render_template("channel.html")


@router.get("/upload")
def upload():
    if "user_id" not in session:
        flash("Для загрузки войдите в аккаунт", category="info")
        return redirect(url_for("auth.login"))
    categories = Category.query.all()
    return render_template("upload.html", categories=categories)


ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/x-msvideo",  # AVI (4V)
    "video/x-ms-wmv",
    "video/quicktime",  # MOV
    "video/x-flv",
    "video/mpeg",
    "video/x-mpeg",
    "video/mpegps",
    "video/3gpp",
    "video/webm",
}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}


@router.post("/upload")
def upload_video():
    if "user_id" not in session:
        return jsonify({"error": "Не авторизованный пользователь"}), 401
    print(request.form.to_dict())

    video_file = request.files.get("video")
    thumbnail_file = request.files.get("thumbnail")

    if video_file.mimetype not in ALLOWED_VIDEO_TYPES:
        return (
            jsonify({"error": "Недопустимый тип видео. Разрешены: MP4, MKV, WebM"}),
            400,
        )
    if thumbnail_file.mimetype not in ALLOWED_IMAGE_TYPES:
        return (
            jsonify({"error": "Недопустимый тип изображения. Разрешены: JPEG, PNG"}),
            400,
        )

    if not video_file or not thumbnail_file:
        return jsonify({"error": "Файлы video и thumbnail обязательны"}), 400

    video_bytes = BytesIO(video_file.read())
    thumbnail_bytes = BytesIO(thumbnail_file.read())

    url, video_id, formatted_duration = convert_video_to_hls(
        video_bytes, thumbnail_bytes
    )

    try:
        tag_ids = request.form.getlist("tags")
        tag_ids = [int(tag) for tag in literal_eval(tag_ids[0])]

        categories = Category.query.filter(Category.category_id.in_(tag_ids)).all()

        new_video = Video(
            video_id=video_id,
            title=request.form.get("title"),
            description=request.form.get("description"),
            url=url,
            duration=formatted_duration,
            categories=categories,
            user_id=session["user_id"],
        )
        db.session.add(new_video)
        db.session.commit()
    except Exception as e:
        print(e)
        jsonify({"error": str(e)}), 500
    return jsonify({"msg": "OK"}), 200


@router.get("/clear_history")
def clear_history():
    user_id = session.get("user_id")

    user = User.query.filter_by(user_id=user_id)

    if user is None:
        return redirect(url_for("auth.login"))

    History.query.filter_by(user_id=user_id).update({"visibility": False})
    db.session.commit()

    return redirect(url_for("routers.get_history"))


@router.get("/save_history")
def save_history():
    user_id = session.get("user_id")
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        flash("Войдите в аккаунт", "danger")
        redirect(url_for("auth.login"))
    try:
        user.retain_history = False
        db.session.commit()
        flash("History has been successfully saved.", "success")
        return redirect(url_for("routers.get_history"))
    except Exception as e:
        print(e)
        db.session.rollback()
        flash(
            "An error occurred while saving history. Please try again later.", "danger"
        )
        return redirect(url_for("routers.get_history"))


@router.get("/liked_video")
def liked_video():
    user_id = session.get("user_id")

    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        return redirect(url_for("auth.login"))

    likes = (
        Rating.query.filter(Rating.user_id == user_id, Rating.rating == True)
        .order_by(desc(Rating.created_at))
        .limit(20)
        .all()
    )
    print(likes)
    first_liked_video = likes[0] if likes else None
    like_count = Rating.query.filter(Rating.user_id == user_id).count()

    return render_template(
        "liked_video.html",
        videos=likes,
        first_liked_video=first_liked_video,
        video_count=like_count,
    )


@router.get("/load_more_videos")
def load_more_videos():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    offset = request.args.get("offset", default=0, type=int)
    limit = 20

    ratings = (
        Rating.query.filter(Rating.user_id == user_id, Rating.rating == True)
        .order_by(desc(Rating.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    videos = []
    for rating in ratings:
        video_data = rating.video.to_dict()
        video_data["views"] = format_views(video_data["views"])
        video_data["created_at"] = time_since_upload(rating.video.created_at)
        videos.append(video_data)
    print(videos)
    return jsonify(videos=videos)


@router.route("/recommendations", methods=["GET"])
def recommendations():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 10))))
    video_id = request.args.get('video_id')
    
    if video_id:
        recommended_videos = (
        db.session.query(Video)
        .filter(Video.valid==True, Video.video_id!=video_id)
        .order_by(db.func.random())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    else:
        recommended_videos = (
        db.session.query(Video)
        .filter_by(valid=True)
        .order_by(db.func.random())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    
    if recommended_videos.items:
        return jsonify(
            {
                "videos": [
                    {
                        "video_id": video.video_id,
                        "title": video.title,
                        "duration": video.duration,
                        "views": video.views,
                        "created_at": time_since_upload(video.created_at),
                        "user": {"username": video.user.username,
                                "user_id": video.user.user_id,
                                "photo_url": video.user.photo_url},
                    }
                    for video in recommended_videos.items
                ],
                "total_pages": recommended_videos.pages,
                "current_page": recommended_videos.page,
            }
        )
    else:
        return jsonify({"message": "No recommendations found"}), 404


@router.get("/comments")
def get_comments():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    video_id = request.args.get("video_id")

    comments = (
        Comment.query.filter_by(video_id=video_id)
        .order_by(Comment.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    result = []
    for comment in comments.items:
        result.append(
            {
                "user": {
                    "username": comment.user.username,
                    "photo_url": comment.user.photo_url,
                },
                "text": comment.text,
                "created_at": time_since_upload(comment.created_at),
            }
        )

    return jsonify({"comments": result})


@router.get("/channel/<int:user_id>")
def get_channel(user_id):
    session_user_id = session.get("user_id")
    channel_user = User.query.filter(User.user_id == user_id).first()
    user = User.query.filter(User.user_id == session_user_id).first()
    
    if user:
        subscribe = Subscription.query.filter(
                Subscription.channel_id == channel_user.user_id,
                Subscription.subscriber_id == user.user_id,
            ).first()
    else:
        subscribe = None
    
    best_video = (
        Video.query.filter(User.user_id == channel_user.user_id, Video.valid == True)
        .order_by(Video.views.desc())
        .first()
    )
    if best_video:
        all_video = Video.query.filter(
            Video.user_id == user_id, Video.video_id != best_video.video_id, Video.valid == True
        ).all()
    else:
        all_video = Video.query.filter(
            Video.user_id == user_id, Video.valid == True).all()
    
    count_video = Video.query.filter_by(user_id=user_id).count()

    return render_template(
        "channel.html",
        user=channel_user,
        best_video=best_video,
        count_video=count_video,
        is_subscribed=subscribe,
        videos=all_video,
    )


@router.route("/settings", methods=["GET", "POST"])
def get_settings():
    user_id = session.get("user_id")
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return redirect(url_for("auth.login"))

    if user.birth_day:
        if isinstance(user.birth_day, datetime):
            user.birth_day = user.birth_day.strftime("%Y-%m-%d")
        else:
            try:
                user.birth_day = datetime.strptime(
                    user.birth_day, "%Y-%m-%d %H:%M:%S"
                ).strftime("%Y-%m-%d")
            except ValueError:
                user.birth_day = ""

    if request.method == "POST":
        try:
            nickname = request.form.get("nickname")
            birth_day = request.form.get("date")
            sex = request.form.get("sex")
            email = request.form.get("email")
            description = request.form.get("description")
            if nickname:
                user.username = nickname
            if birth_day:
                user.birth_day = datetime.strptime(birth_day, "%Y-%m-%d")
            if sex in ["male", "female"]:
                user.sex = sex
            if email:
                user.email = email
            if description:
                user.description = description

            db.session.commit()
            return redirect(url_for("routers.get_settings"))
        except Exception as e:
            print(e)
            db.session.rollback()
            return redirect(url_for("routers.get_settings"))

    return render_template(
        "settings.html",
        user=user,
    )


@router.get("/get_photo/<string:photo_url>")
def get_photo(photo_url):
    photo_path = os.path.join("static", "images", "photo_url", photo_url)
    if os.path.exists(photo_path):
        return send_file(photo_path)
    else:
        return jsonify({"error": "Нет фотографии"}), 404


@router.post("/update_user_photo")
def update_photo():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    photo = request.files["photo"]

    if not photo.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        flash("Invalid file type. Only PNG, JPG, and JPEG are allowed.", "error")
        return redirect(url_for("routers.get_settings"))

    filename = f"user_{user_id}__{uuid4()}.jpg"
    save_path = os.path.join("static/images/photo_url", filename)

    upload_folder = os.path.dirname(save_path)
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    try:
        photo.save(save_path)

        user = User.query.filter_by(user_id=user_id).first()
        if user.photo_url:
            old_photo_path = os.path.join("static/images/photo_url", user.photo_url)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)

        user.photo_url = filename
        db.session.commit()

        flash("Фото успешно обновлено!", "success")
        return redirect(url_for("routers.get_settings"))
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при обновлении фото: {str(e)}", "error")
        return redirect(url_for("routers.get_settings"))


@router.post("/delete_user_photo")
def delete_photo():
    user_id = session.get("user_id")
    if not user_id:
        flash("Не автрризированный", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(user_id=user_id).first()
    if not user or not user.photo_url:
        flash("Файл не найден", "error")
        return redirect(url_for("routers.get_settings"))

    try:
        photo_path = os.path.join("static/uploads", user.photo_url)
        if os.path.exists(photo_path):
            os.remove(photo_path)

        user.photo_url = None
        db.session.commit()

        flash("Фото успешно обновлено!", "success")
        return redirect(url_for("routers.get_settings"))
    except Exception as e:
        flash(f"Ошибка при удалении фото: {str(e)}", "error")
        return redirect(url_for("routers.get_settings"))


@router.get("/confidentiality")
def confidentiality():
    return render_template("confidentiality.html")


@router.get("/agreement")
def agreement():
    return render_template("agreement.html")


@router.route("/my_video", methods=["GET"])
def my_video():
    h1 = "Мои видео"
    user_id = session.get("user_id")
    user = User.query.filter(User.user_id == user_id).first()
    videos = Video.query.all()
    for video in videos:
        video.create_at = time_since_upload(video.created_at)
    return render_template("my_video.html", user=user, videos=videos, h1=h1)


@router.get("/edit_video/<string:video_id>")
def edit_video(video_id):
    user_id = session.get("user_id")
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        redirect(url_for("auth.login"))
    video = Video.query.filter(Video.video_id == video_id).first()
    categories = Category.query.all()
    return render_template("edit.html", video=video, categories=categories)


@router.post("/edit_video/<string:video_id>")
def edit_infornation(video_id):
    user_id = session.get("user_id")
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        return redirect(url_for("auth.login"))

    video = Video.query.filter(Video.video_id == video_id).first()

    if not video:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        tags = json.loads(request.form["tags"])
        print(tags)
        audience = request.form.get("audience")
        age_restriction = request.form.get("age_restriction")

        video.title = title
        video.description = description
        video.audience = audience
        video.age_restriction = age_restriction

        video.categories.clear()
        for category_id in tags:
            category = Category.query.filter_by(category_id=category_id).first()
            if category:
                video.categories.append(category)

        if "thumbnail" in request.files:
            thumbnail = request.files["thumbnail"]
            if thumbnail and thumbnail.filename != "":
                thumbnail_path = f"{video.url}/thumbnail.jpg"
                thumbnail.save(thumbnail_path)
                video.thumbnail = thumbnail_path

        db.session.commit()

        return jsonify({"success": True, "msg": "Ok"}), 200


@router.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if query:
        print(f"Search Query: {query}")
        results = Video.query.filter(Video.title.ilike(f"%{query}%")).all()
        print(f"Results: {results}")
    else:
        results = []
    return render_template('category.html', query=query, videos=results, h1='Найденные совпадения')


@router.route("/category_page/<string:category_name>")
def category_page(category_name):
    
    if category_name == 'valid':
        user_id = session.get('user_id')
        videos = Video.query.filter(Video.valid==False).order_by(Video.views.asc()).all()
        return render_template('category.html', videos=videos, h1="Невалидированные")
        
    elif category_name == 'subscribers':
        user_id = session.get('user_id')
        subscribed_users = db.session.query(Subscription.channel_id).filter(Subscription.subscriber_id == user_id).all()
        videos = Video.query.filter(Video.user_id.in_([user[0] for user in subscribed_users])).order_by(Video.views.asc()).all()
        return render_template('category.html', videos=videos, h1="Подписки")
    
    elif category_name == 'trending_up':
        videos = Video.query.filter().order_by(Video.views.asc()).all()
        return render_template('category.html', videos=videos, h1="Тренды")
    
    category = Category.query.filter(Category.category_name == category_name).first()

    if category:
        videos = Video.query.filter(Video.categories.contains(category)).all()
        return render_template('category.html', category=category, videos=videos, h1=category_name)
    abort(404)
    

@router.route('/valid_video/<string:video_id>/<int:action>')
def valid_video(video_id, action):
    video = Video.query.filter_by(video_id=video_id).first()
    
    if action==1:
        video.valid = True
        db.session.commit()
        
    elif action==2:
        db.session.delete(video)
        db.session.commit()
        
    return redirect(url_for('routers.category_page', category_name='valid'))