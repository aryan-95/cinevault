"""Tracks per-user playback progress for the Continue Watching feature."""

from datetime import datetime

from app import db


class WatchHistory(db.Model):
    __tablename__ = "watch_history"
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_watch_user_movie"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)

    progress_seconds = db.Column(db.Integer, default=0, nullable=False)
    duration_seconds = db.Column(db.Integer, default=0, nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    last_watched = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def completion_percentage(self) -> float:
        if not self.duration_seconds:
            return 0.0
        return round(min(self.progress_seconds / self.duration_seconds, 1.0) * 100, 1)

    def __repr__(self) -> str:
        return f"<WatchHistory user={self.user_id} movie={self.movie_id} progress={self.progress_seconds}>"
