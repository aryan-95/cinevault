"""User's personal watchlist ("My List")."""

from datetime import datetime

from app import db


class MyListEntry(db.Model):
    __tablename__ = "my_list"
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_mylist_user_movie"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<MyListEntry user={self.user_id} movie={self.movie_id}>"
