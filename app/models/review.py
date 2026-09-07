"""Star ratings and written reviews left by users on movies."""

from datetime import datetime

from app import db


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_review_user_movie"),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)

    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=True, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Review user={self.user_id} movie={self.movie_id} rating={self.rating}>"
