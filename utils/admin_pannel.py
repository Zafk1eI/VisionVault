from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask import session, redirect, url_for
from models.models import User, Video, Rating, Subscription, History, Category, Comment

from utils.db_init import db
from models.enums import Role


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if "user_id" not in session:
            print("User not logged in.")
            return False

        user_id = session["user_id"]
        user = User.query.filter_by(user_id=user_id).first()

        if user and user.role == Role.ADMIN:
            return True
        print(f"User {user_id} is not admin.")
        return False

    def inaccessible_callback(self, name, **kwargs):
        print("Redirecting to index.")
        return redirect(url_for("auth.login"))


admin = Admin(
    name="VisionVault",
    index_view=MyAdminIndexView(name="Главная", url="/admin"),
    template_mode="bootstrap4",
)


from wtforms import SelectField


class UserModelView(ModelView):
    form_overrides = {
        'role': SelectField
    }
    form_args = {
        'role': {
            'choices': [(role.name, role.value) for role in Role]
        }
    }
    column_list = ['username', 'email', 'role', 'created_at']
    column_searchable_list = ['username', 'email']

    def on_model_change(self, form, model, is_created):
        if is_created or model.password != form.password.data:
            model.set_password(form.password.data)
        return super().on_model_change(form, model, is_created)


class VideoModelView(ModelView):
    column_searchable_list = ["title", "description"]
    column_editable_list = [
        "title",
        "description",
        "duration",
        "views",
        "likes",
        "dislikes",
    ]
    form_columns = ["title", "description", "url", "duration"]
    can_delete = True
    can_create = True
    can_view_details = True


class HistoryModelView(ModelView):
    column_filters = ["visibility"]
    column_editable_list = ["visibility"]
    form_columns = ["user", "video", "visibility"]
    can_delete = True
    can_create = True
    can_view_details = True


class RatingModelView(ModelView):
    column_searchable_list = ["user.username", "video.title"]
    column_filters = ["rating"]
    column_editable_list = ["rating"]
    form_columns = ["user", "video", "rating"]
    can_delete = True
    can_create = True
    can_view_details = True


class CommentModelView(ModelView):
    column_searchable_list = ["user.username", "video.title", "text"]
    column_filters = ["created_at"]
    column_editable_list = ["text"]
    form_columns = ["user", "video", "text"]
    can_delete = True
    can_create = True
    can_view_details = True


class SubscriptionModelView(ModelView):
    column_searchable_list = ["subscriber.username", "channel.username"]
    column_filters = ["created_at"]
    form_columns = ["subscriber", "channel"]
    can_delete = True
    can_create = True
    can_view_details = True


class CategoryModelView(ModelView):
    column_searchable_list = ["category_name"]
    column_editable_list = ["category_name"]
    form_columns = ["category_name"]
    can_delete = True
    can_create = True
    can_view_details = True


admin = Admin(name="VisionVault", template_mode="bootstrap4")

admin.add_view(UserModelView(User, db.session, name="Пользователи"))
admin.add_view(VideoModelView(Video, db.session, name="Видео"))
admin.add_view(CategoryModelView(Category, db.session, name="Категории"))
admin.add_view(HistoryModelView(History, db.session, name="История просмотров"))
admin.add_view(RatingModelView(Rating, db.session, name="Рейтинги"))
admin.add_view(CommentModelView(Comment, db.session, name="Комментарии"))
admin.add_view(SubscriptionModelView(Subscription, db.session, name="Подписки"))
