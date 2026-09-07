"""JSON REST API for CineVault (used by the frontend JS and external clients)."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from app import csrf, db
from app.decorators import admin_required
from app.models.movie import Movie
from app.models.my_list import MyListEntry
from app.models.review import Review
from app.models.user import User
from app.models.watch_history import WatchHistory

api_bp = Blueprint("api", __name__)


def _movie_to_dict(movie: Movie) -> dict:
    return {
        "id": movie.id,
        "title": movie.title,
        "description": movie.description,
        "release_year": movie.release_year,
        "duration_minutes": movie.duration_minutes,
        "genre": movie.genre_list,
        "language": movie.language,
        "age_rating": movie.age_rating,
        "cast": movie.cast,
        "director": movie.director,
        "poster_url": movie.poster_url,
        "backdrop_url": movie.backdrop_url,
        "video_url": movie.video_url,
        "trailer_url": movie.trailer_url,
        "average_rating": movie.average_rating,
        "rating_count": movie.rating_count,
        "view_count": movie.view_count,
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@api_bp.route("/auth/register", methods=["POST"])
@csrf.exempt
def register():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or len(password) < 8:
        return jsonify({"error": "username, email, and a password of 8+ chars are required."}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 201


@api_bp.route("/auth/login", methods=["POST"])
@csrf.exempt
def login():
    data = request.get_json(silent=True) or request.form
    identifier = (data.get("identifier") or data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()
    if not user or not user.check_password(password) or not user.is_active:
        return jsonify({"error": "Invalid credentials."}), 401

    login_user(user)
    return jsonify({"id": user.id, "username": user.username, "role": user.role.value})


@api_bp.route("/auth/logout", methods=["POST"])
@csrf.exempt
@login_required
def logout():
    logout_user()
    return jsonify({"status": "logged out"})


# ---------------------------------------------------------------------------
# Movies
# ---------------------------------------------------------------------------

@api_bp.route("/movies", methods=["GET"])
def list_movies():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    pagination = Movie.query.order_by(Movie.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
        "movies": [_movie_to_dict(m) for m in pagination.items],
    })


@api_bp.route("/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    return jsonify(_movie_to_dict(movie))


@api_bp.route("/movies", methods=["POST"])
@login_required
@admin_required
def create_movie():
    data = request.get_json(silent=True) or request.form
    if not data.get("title"):
        return jsonify({"error": "title is required."}), 400

    movie = Movie(
        title=data.get("title"),
        description=data.get("description", ""),
        release_year=int(data.get("release_year", 2024)),
        duration_minutes=int(data.get("duration_minutes", 90)),
        genre=data.get("genre", ""),
        language=data.get("language", "English"),
        age_rating=data.get("age_rating", "PG-13"),
        cast=data.get("cast", ""),
        director=data.get("director", ""),
        poster_url=data.get("poster_url", ""),
        backdrop_url=data.get("backdrop_url", ""),
        video_url=data.get("video_url", ""),
        trailer_url=data.get("trailer_url", ""),
    )
    db.session.add(movie)
    db.session.commit()
    return jsonify(_movie_to_dict(movie)), 201


@api_bp.route("/movies/<int:movie_id>", methods=["PUT"])
@login_required
@admin_required
def update_movie(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    data = request.get_json(silent=True) or request.form

    for field in (
        "title", "description", "genre", "language", "age_rating",
        "cast", "director", "poster_url", "backdrop_url", "video_url", "trailer_url",
    ):
        if field in data:
            setattr(movie, field, data[field])

    for int_field in ("release_year", "duration_minutes"):
        if int_field in data:
            setattr(movie, int_field, int(data[int_field]))

    db.session.commit()
    return jsonify(_movie_to_dict(movie))


@api_bp.route("/movies/<int:movie_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_movie(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return jsonify({"status": "deleted"})


# ---------------------------------------------------------------------------
# Search & genres
# ---------------------------------------------------------------------------

@api_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    movie_query = Movie.query
    if query:
        like_pattern = f"%{query}%"
        movie_query = movie_query.filter(
            (Movie.title.ilike(like_pattern))
            | (Movie.genre.ilike(like_pattern))
            | (Movie.cast.ilike(like_pattern))
            | (Movie.director.ilike(like_pattern))
        )
    movies = movie_query.limit(50).all()
    return jsonify({"results": [_movie_to_dict(m) for m in movies]})


@api_bp.route("/genres/<genre_name>", methods=["GET"])
def genre_movies(genre_name: str):
    movies = Movie.query.filter(Movie.genre.ilike(f"%{genre_name}%")).all()
    return jsonify({"genre": genre_name, "movies": [_movie_to_dict(m) for m in movies]})


# ---------------------------------------------------------------------------
# My List
# ---------------------------------------------------------------------------

@api_bp.route("/my-list", methods=["GET"])
@login_required
def get_my_list():
    entries = MyListEntry.query.filter_by(user_id=current_user.id).all()
    return jsonify({"movies": [_movie_to_dict(e.movie) for e in entries if e.movie]})


@api_bp.route("/my-list/<int:movie_id>", methods=["POST"])
@login_required
def api_add_to_list(movie_id: int):
    Movie.query.get_or_404(movie_id)
    if not MyListEntry.query.filter_by(user_id=current_user.id, movie_id=movie_id).first():
        db.session.add(MyListEntry(user_id=current_user.id, movie_id=movie_id))
        db.session.commit()
    return jsonify({"status": "added"}), 201


@api_bp.route("/my-list/<int:movie_id>", methods=["DELETE"])
@login_required
def api_remove_from_list(movie_id: int):
    entry = MyListEntry.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return jsonify({"status": "removed"})


# ---------------------------------------------------------------------------
# Watch history / progress
# ---------------------------------------------------------------------------

@api_bp.route("/watch-history", methods=["GET"])
@login_required
def watch_history():
    entries = WatchHistory.query.filter_by(user_id=current_user.id).order_by(
        WatchHistory.last_watched.desc()
    ).all()
    return jsonify({
        "history": [
            {
                "movie_id": e.movie_id,
                "movie_title": e.movie.title if e.movie else None,
                "progress_seconds": e.progress_seconds,
                "duration_seconds": e.duration_seconds,
                "completed": e.completed,
                "completion_percentage": e.completion_percentage,
                "last_watched": e.last_watched.isoformat() if e.last_watched else None,
            }
            for e in entries
        ]
    })


@api_bp.route("/watch-progress", methods=["POST"])
@login_required
def watch_progress():
    data = request.get_json(silent=True) or request.form
    movie_id = data.get("movie_id")
    if not movie_id:
        return jsonify({"error": "movie_id is required."}), 400

    movie = Movie.query.get_or_404(int(movie_id))
    history = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie.id).first()
    if not history:
        history = WatchHistory(user_id=current_user.id, movie_id=movie.id)
        db.session.add(history)

    history.progress_seconds = int(float(data.get("progress_seconds", 0)))
    history.duration_seconds = int(float(data.get("duration_seconds", history.duration_seconds or 0)))
    if history.duration_seconds and history.progress_seconds >= history.duration_seconds * 0.95:
        history.completed = True

    db.session.commit()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@api_bp.route("/reviews", methods=["POST"])
@login_required
def create_review():
    data = request.get_json(silent=True) or request.form
    movie_id = data.get("movie_id")
    rating = data.get("rating")

    if not movie_id or rating is None:
        return jsonify({"error": "movie_id and rating are required."}), 400

    rating = int(rating)
    if rating < 1 or rating > 5:
        return jsonify({"error": "rating must be between 1 and 5."}), 400

    movie = Movie.query.get_or_404(int(movie_id))
    existing = Review.query.filter_by(user_id=current_user.id, movie_id=movie.id).first()
    if existing:
        return jsonify({"error": "You already reviewed this movie. Use PUT to update it."}), 409

    review = Review(
        user_id=current_user.id,
        movie_id=movie.id,
        rating=rating,
        review_text=data.get("review_text", ""),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"id": review.id, "rating": review.rating}), 201


@api_bp.route("/reviews/<int:review_id>", methods=["PUT"])
@login_required
def update_review(review_id: int):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        return jsonify({"error": "Not authorized to edit this review."}), 403

    data = request.get_json(silent=True) or request.form
    if "rating" in data:
        rating = int(data["rating"])
        if rating < 1 or rating > 5:
            return jsonify({"error": "rating must be between 1 and 5."}), 400
        review.rating = rating
    if "review_text" in data:
        review.review_text = data["review_text"]

    db.session.commit()
    return jsonify({"id": review.id, "rating": review.rating})


@api_bp.route("/reviews/<int:review_id>", methods=["DELETE"])
@login_required
def delete_review(review_id: int):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Not authorized to delete this review."}), 403

    db.session.delete(review)
    db.session.commit()
    return jsonify({"status": "deleted"})
