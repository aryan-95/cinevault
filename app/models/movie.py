"""Movie catalog model."""

from datetime import datetime

from app import db


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False, default="")
    release_year = db.Column(db.Integer, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=90)

    # Comma separated genre list, e.g. "Action,Sci-Fi"
    genre = db.Column(db.String(200), nullable=False, default="", index=True)
    language = db.Column(db.String(50), nullable=False, default="English")
    age_rating = db.Column(db.String(10), nullable=False, default="PG-13")

    cast = db.Column(db.String(500), nullable=False, default="")
    director = db.Column(db.String(120), nullable=False, default="")

    poster_url = db.Column(db.String(300), nullable=False, default="")
    backdrop_url = db.Column(db.String(300), nullable=False, default="")
    video_url = db.Column(db.String(300), nullable=False, default="")
    trailer_url = db.Column(db.String(300), nullable=False, default="")
    subtitle_url = db.Column(db.String(300), nullable=True)

    is_trending = db.Column(db.Boolean, default=False, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    reviews = db.relationship(
        "Review", backref="movie", lazy="dynamic", cascade="all, delete-orphan"
    )
    watch_entries = db.relationship(
        "WatchHistory", backref="movie", lazy="dynamic", cascade="all, delete-orphan"
    )
    list_entries = db.relationship(
        "MyListEntry", backref="movie", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def genre_list(self) -> list[str]:
        return [g.strip() for g in self.genre.split(",") if g.strip()]

    @property
    def average_rating(self) -> float:
        ratings = [r.rating for r in self.reviews]
        if not ratings:
            return 0.0
        return round(sum(ratings) / len(ratings), 1)

    @property
    def rating_count(self) -> int:
        return self.reviews.count()

    @property
    def duration_display(self) -> str:
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def __repr__(self) -> str:
        return f"<Movie {self.title} ({self.release_year})>"
