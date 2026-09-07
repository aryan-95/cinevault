"""User model with role-based access control."""

import enum
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active_flag = db.Column("is_active", db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    watch_history = db.relationship(
        "WatchHistory", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    my_list_entries = db.relationship(
        "MyListEntry", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    reviews = db.relationship(
        "Review", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    # flask-login uses `is_active`; expose our column under that name too
    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return self.is_active_flag

    def __repr__(self) -> str:
        return f"<User {self.username}>"
