from flask_migrate import Migrate

from models.models import (
    Category, User,
    Video, Comment,
    Rating, Subscription,
    VideoCategories, History, Session
)

migrate = Migrate()


