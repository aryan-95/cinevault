"""Homepage, search, genre browsing, and My List pages."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template, request, send_from_directory
from flask_login import current_user, login_required

from app.models.movie import Movie
from app.models.my_list import MyListEntry
from app.models.watch_history import WatchHistory
from app.services.recommendation_service import get_recommendations_for_user

main_bp = Blueprint("main", __name__)

GENRES = [
    "Action", "Comedy", "Drama", "Sci-Fi", "Thriller", "Horror",
    "Romance", "Animation", "Documentary", "Fantasy",
]


@main_bp.route("/media/<path:filename>")
def media(filename: str):
    """Serve locally-stored uploads (posters, backdrops, videos, subtitles).

    In production this route would be replaced by direct CDN/S3 URLs --
    see `app/services/storage_service.py`.
    """
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@main_bp.route("/")
def index():
    featured = Movie.query.filter_by(is_featured=True).order_by(Movie.created_at.desc()).first()
    if not featured:
        featured = Movie.query.order_by(Movie.created_at.desc()).first()

    trending = Movie.query.filter_by(is_trending=True).order_by(Movie.view_count.desc()).limit(12).all()
    popular = Movie.query.order_by(Movie.view_count.desc()).limit(12).all()
    recently_added = Movie.query.order_by(Movie.created_at.desc()).limit(12).all()

    genre_rows = {}
    for genre in ("Action", "Comedy", "Drama", "Sci-Fi", "Thriller", "Horror"):
        genre_rows[genre] = Movie.query.filter(Movie.genre.ilike(f"%{genre}%")).limit(12).all()

    continue_watching = []
    recommended = []
    if current_user.is_authenticated:
        history_entries = (
            WatchHistory.query.filter_by(user_id=current_user.id, completed=False)
            .filter(WatchHistory.progress_seconds > 0)
            .order_by(WatchHistory.last_watched.desc())
            .limit(12)
            .all()
        )
        continue_watching = [(entry.movie, entry) for entry in history_entries if entry.movie]
        recommended = get_recommendations_for_user(current_user.id, limit=12)

    return render_template(
        "index.html",
        featured=featured,
        trending=trending,
        popular=popular,
        recently_added=recently_added,
        genre_rows=genre_rows,
        continue_watching=continue_watching,
        recommended=recommended,
    )


@main_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    genre_filter = request.args.get("genre", "").strip()
    year_filter = request.args.get("year", "").strip()
    rating_filter = request.args.get("rating", "").strip()
    language_filter = request.args.get("language", "").strip()
    page = request.args.get("page", 1, type=int)

    movie_query = Movie.query

    if query:
        like_pattern = f"%{query}%"
        movie_query = movie_query.filter(
            (Movie.title.ilike(like_pattern))
            | (Movie.genre.ilike(like_pattern))
            | (Movie.cast.ilike(like_pattern))
            | (Movie.director.ilike(like_pattern))
            | (Movie.description.ilike(like_pattern))
        )

    if genre_filter:
        movie_query = movie_query.filter(Movie.genre.ilike(f"%{genre_filter}%"))
    if year_filter.isdigit():
        movie_query = movie_query.filter(Movie.release_year == int(year_filter))
    if language_filter:
        movie_query = movie_query.filter(Movie.language.ilike(language_filter))

    movies = movie_query.order_by(Movie.created_at.desc()).all()

    if rating_filter:
        try:
            min_rating = float(rating_filter)
            movies = [m for m in movies if m.average_rating >= min_rating]
        except ValueError:
            pass

    per_page = 12
    total = len(movies)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_movies = movies[start:end]
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "search.html",
        movies=paginated_movies,
        query=query,
        genres=GENRES,
        page=page,
        total_pages=total_pages,
        total=total,
        filters={
            "genre": genre_filter,
            "year": year_filter,
            "rating": rating_filter,
            "language": language_filter,
        },
    )


@main_bp.route("/genre/<genre_name>")
def genre(genre_name: str):
    movies = Movie.query.filter(Movie.genre.ilike(f"%{genre_name}%")).order_by(
        Movie.created_at.desc()
    ).all()
    return render_template("genre.html", movies=movies, genre_name=genre_name, genres=GENRES)


@main_bp.route("/my-list")
@login_required
def my_list():
    entries = MyListEntry.query.filter_by(user_id=current_user.id).order_by(
        MyListEntry.created_at.desc()
    ).all()
    movies = [entry.movie for entry in entries if entry.movie]
    return render_template("my_list.html", movies=movies)
