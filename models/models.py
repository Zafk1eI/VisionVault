from __future__ import annotations

from datetime import timezone, datetime, timedelta
from typing import List

from sqlalchemy.orm import Mapped
from werkzeug.security import check_password_hash, generate_password_hash

from utils.db_init import db
from models.enums import Role


class User(db.Model):
    __tablename__ = "Users"  

    user_id: Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = db.mapped_column(db.String(45), nullable=False, unique=True)
    email: Mapped[str] = db.mapped_column(db.String(100), nullable=False, unique=True)
    photo_url: Mapped[str] = db.mapped_column(nullable=True)
    password: Mapped[str] = db.mapped_column(db.String(255), nullable=False)
    description: Mapped[str] = db.mapped_column(nullable=True)
    sex: Mapped[str] = db.mapped_column(nullable=True)
    birth_day: Mapped[datetime] = db.mapped_column(nullable=True)
    created_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc))
    update_at: Mapped[datetime] = db.mapped_column(
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    retain_history: Mapped[bool] = db.mapped_column(default=True)
    role: Mapped[Role] = db.mapped_column(
        db.Enum(Role, name="role_enum", create_type=False),
        nullable=False,
        default=Role.USER,
    )
    videos: Mapped[List["Video"]] = db.relationship("Video", back_populates="user")
    user_history: Mapped[List["History"]] = db.relationship(
        "History", back_populates="user"
    )
    rated_videos: Mapped[List["Rating"]] = db.relationship(
        "Rating", back_populates="user"
    )
    comments: Mapped[List["Comment"]] = db.relationship(
        "Comment", back_populates="user"
    )

    subscriptions: Mapped[List["Subscription"]] = db.relationship(
        "Subscription",
        back_populates="subscriber",
        foreign_keys="[Subscription.subscriber_id]",
    )

    channels: Mapped[List["Subscription"]] = db.relationship(
        "Subscription",
        back_populates="channel",
        foreign_keys="[Subscription.channel_id]",
    )
    
    sessions: Mapped[List["Session"]] = db.relationship("Session", back_populates="user")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "photo_url": self.photo_url,
            "created_at": self.created_at,
            "updated_at": self.update_at,
        }

    def set_password(self, password):
        self.password = generate_password_hash(password, salt_length=3)

    def valid_password_hash(self, password):
        try:
            return check_password_hash(self.password, password)
        except Exception as e:
            print(f"Password validation error: {str(e)}")
            return False

    def __str__(self):
        return self.email


class Video(db.Model):
    __tablename__ = "Videos"

    video_id: Mapped[str] = db.mapped_column(primary_key=True)
    title: Mapped[str] = db.mapped_column(nullable=False)
    description: Mapped[str] = db.mapped_column(nullable=False)
    views: Mapped[int] = db.mapped_column(default=0)
    url: Mapped[str] = db.mapped_column(nullable=False)
    duration: Mapped[str] = db.mapped_column(nullable=False)
    likes: Mapped[int] = db.mapped_column(default=0)
    valid: Mapped[bool] = db.mapped_column(default=0)
    dislikes: Mapped[int] = db.mapped_column(default=0)
    created_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc))
    update_at: Mapped[datetime] = db.mapped_column(
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    user_id: Mapped[int] = db.mapped_column(db.ForeignKey("Users.user_id"))
    user: Mapped[User] = db.relationship("User", back_populates="videos")
    history: Mapped[List["History"]] = db.relationship(
        "History", back_populates="video"
    )
    ratings: Mapped[List["Rating"]] = db.relationship("Rating", back_populates="video")
    comments: Mapped[List["Comment"]] = db.relationship(
        "Comment", back_populates="video"
    )
    categories: Mapped[List["Category"]] = db.relationship(
        "Category", secondary="video_categories", back_populates="videos"
    )

    def to_dict(self):
        return {
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "views": self.views,
            "duration": self.duration,
            "url": self.url,
            "username": self.user.username,
            "created_at": self.created_at,
        }

    def __str__(self):
        return self.title


class History(db.Model):
    __tablename__ = "Histories"

    history_id: Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    video_id: Mapped[str] = db.mapped_column(
        db.ForeignKey("Videos.video_id"), nullable=False
    )
    user_id: Mapped[int] = db.mapped_column(
        db.ForeignKey("Users.user_id"), nullable=False
    )
    visibility: Mapped[bool] = db.mapped_column(nullable=False)
    viewed_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc))

    video: Mapped["Video"] = db.relationship("Video", back_populates="history")
    user: Mapped["User"] = db.relationship("User", back_populates="user_history")


class Rating(db.Model):
    __tablename__ = "Ratings"

    rating_id: Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    rating: Mapped[bool] = db.mapped_column(nullable=False)
    created_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc))
    update_at: Mapped[datetime] = db.mapped_column(
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    user_id: Mapped[int] = db.mapped_column(
        db.ForeignKey("Users.user_id"), nullable=False
    )
    video_id: Mapped[str] = db.mapped_column(
        db.ForeignKey("Videos.video_id"), nullable=False
    )

    user: Mapped["User"] = db.relationship("User", back_populates="rated_videos")
    video: Mapped["Video"] = db.relationship("Video", back_populates="ratings")

    def to_dict(self):
        return {
            'rating_id': self.rating_id,
            'rating': self.rating,
            'created_at': self.created_at,
            'updated_at': self.update_at,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'video': self.video.to_dict() 
        }

class Comment(db.Model):
    __tablename__ = "Comments"

    comment_id: Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = db.mapped_column(nullable=False)
    user_id: Mapped[int] = db.mapped_column(
        db.ForeignKey("Users.user_id"), nullable=False
    )
    video_id: Mapped[str] = db.mapped_column(
        db.ForeignKey("Videos.video_id"), nullable=False
    )
    created_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc))
    update_at: Mapped[datetime] = db.mapped_column(
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )

    user: Mapped["User"] = db.relationship("User", back_populates="comments")
    video: Mapped["Video"] = db.relationship("Video", back_populates="comments")

    def to_dict(self):
        return {
            "comment_id": self.comment_id,
            "text": self.text,
            "user_id": self.user_id,
            "video_id": self.video_id,
        }


class Subscription(db.Model):
    __tablename__ = "Subscriptions"

    id: Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    subscriber_id: Mapped[int] = db.mapped_column(
        db.ForeignKey("Users.user_id"), nullable=False
    )
    channel_id: Mapped[int] = db.mapped_column(
        db.ForeignKey("Users.user_id"), nullable=False
    )
    created_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc))
    update_at: Mapped[datetime] = db.mapped_column(
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )

    subscriber: Mapped["User"] = db.relationship(
        "User", foreign_keys=[subscriber_id], back_populates="subscriptions"
    )
    channel: Mapped["User"] = db.relationship(
        "User", foreign_keys=[channel_id], back_populates="channels"
    )

    __table_args__ = (
        db.UniqueConstraint("subscriber_id", "channel_id", name="unique_subscription"),
    )


class Category(db.Model):
    __tablename__ = "Categories"

    category_id: Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    category_name: Mapped[str] = db.mapped_column(nullable=False)
    videos: Mapped[List["Video"]] = db.relationship(
        "Video", secondary="video_categories", back_populates="categories"
    )

    def __str__(self):
        return self.categoty_name
    

class VideoCategories(db.Model):
    __tablename__ = "video_categories"

    video_id: Mapped[str] = db.mapped_column(
        db.ForeignKey("Videos.video_id"), primary_key=True
    )
    category_id: Mapped[int] = db.mapped_column(
        db.ForeignKey("Categories.category_id"), primary_key=True
    )


class Session(db.Model):
    __tablename__ = "Sessions" 

    session_id: Mapped[int] = db.mapped_column(db.Integer, primary_key=True, unique=True, autoincrement=True, nullable=False)
    user_id: Mapped[int] = db.mapped_column( db.ForeignKey('Users.user_id'), nullable=False)
    session_token: Mapped[str] = db.mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc)) 
    expires_at: Mapped[datetime] = db.mapped_column(default=datetime.now(timezone.utc) + timedelta(days=7), nullable=False)
    
    user: Mapped['User'] = db.relationship("User", back_populates="sessions")


    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at

    def refresh(self):
        self.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
    def __str__(self):
        return self.session_token
    
