"""Admin dashboard: analytics, movie management, and user management."""

from __future__ import annotations

import os

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.models.movie import Movie
from app.models.review import Review
from app.models.user import User, UserRole
from app.models.watch_history import WatchHistory
from app.services.storage_service import allowed_file, get_storage_service

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
def require_admin():
    """Runs before every route in this blueprint: only admins may proceed."""
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@admin_bp.route("/")
def dashboard():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active_flag=True).count()
    total_movies = Movie.query.count()
    total_watch_sessions = WatchHistory.query.count()

    most_watched = Movie.query.order_by(Movie.view_count.desc()).limit(5).all()
    recently_added = Movie.query.order_by(Movie.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        active_users=active_users,
        total_movies=total_movies,
        total_watch_sessions=total_watch_sessions,
        most_watched=most_watched,
        recently_added=recently_added,
    )


# ---------------------------------------------------------------------------
# Movie management
# ---------------------------------------------------------------------------

@admin_bp.route("/movies")
def movie_list():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template("admin/movies.html", movies=movies)


@admin_bp.route("/movies/new", methods=["GET", "POST"])
def movie_new():
    if request.method == "POST":
        movie = Movie(title="")
        _apply_movie_form(movie, request)
        db.session.add(movie)
        db.session.commit()
        flash(f'Movie "{movie.title}" created.', "success")
        return redirect(url_for("admin.movie_list"))
    return render_template("admin/movie_form.html", movie=None)


@admin_bp.route("/movies/<int:movie_id>/edit", methods=["GET", "POST"])
def movie_edit(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == "POST":
        _apply_movie_form(movie, request)
        db.session.commit()
        flash(f'Movie "{movie.title}" updated.', "success")
        return redirect(url_for("admin.movie_list"))
    return render_template("admin/movie_form.html", movie=movie)


@admin_bp.route("/movies/<int:movie_id>/delete", methods=["POST"])
def movie_delete(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash("Movie deleted.", "info")
    return redirect(url_for("admin.movie_list"))


def _apply_movie_form(movie: Movie, req) -> None:
    """Populate a Movie instance from an admin form submission, including uploads."""
    form = req.form
    movie.title = form.get("title", movie.title)
    movie.description = form.get("description", movie.description)
    movie.release_year = int(form.get("release_year") or movie.release_year or 2024)
    movie.duration_minutes = int(form.get("duration_minutes") or movie.duration_minutes or 90)
    movie.genre = form.get("genre", movie.genre)
    movie.language = form.get("language", movie.language)
    movie.age_rating = form.get("age_rating", movie.age_rating)
    movie.cast = form.get("cast", movie.cast)
    movie.director = form.get("director", movie.director)
    movie.trailer_url = form.get("trailer_url", movie.trailer_url)
    movie.is_trending = bool(form.get("is_trending"))
    movie.is_featured = bool(form.get("is_featured"))

    storage = get_storage_service(current_app.config["UPLOAD_FOLDER"])

    poster_file = req.files.get("poster_file")
    if poster_file and poster_file.filename:
        if allowed_file(poster_file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
            movie.poster_url = storage.save(poster_file, "posters")
        else:
            flash("Poster file type not allowed.", "danger")

    backdrop_file = req.files.get("backdrop_file")
    if backdrop_file and backdrop_file.filename:
        if allowed_file(backdrop_file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
            movie.backdrop_url = storage.save(backdrop_file, "backdrops")
        else:
            flash("Backdrop file type not allowed.", "danger")

    video_file = req.files.get("video_file")
    if video_file and video_file.filename:
        if allowed_file(video_file.filename, current_app.config["ALLOWED_VIDEO_EXTENSIONS"]):
            movie.video_url = storage.save(video_file, "movies")
        else:
            flash("Video file type not allowed.", "danger")

    subtitle_file = req.files.get("subtitle_file")
    if subtitle_file and subtitle_file.filename:
        if allowed_file(subtitle_file.filename, current_app.config["ALLOWED_SUBTITLE_EXTENSIONS"]):
            movie.subtitle_url = storage.save(subtitle_file, "subtitles")
        else:
            flash("Subtitle file type not allowed.", "danger")

    # Allow pasting a direct URL instead of uploading, useful for demo/seed data
    if form.get("poster_url"):
        movie.poster_url = form.get("poster_url")
    if form.get("backdrop_url"):
        movie.backdrop_url = form.get("backdrop_url")
    if form.get("video_url"):
        movie.video_url = form.get("video_url")


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@admin_bp.route("/users")
def user_list():
    query = request.args.get("q", "").strip()
    users_query = User.query
    if query:
        like_pattern = f"%{query}%"
        users_query = users_query.filter(
            (User.username.ilike(like_pattern)) | (User.email.ilike(like_pattern))
        )
    users = users_query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, query=query)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
def user_toggle_active(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot disable your own account.", "danger")
        return redirect(url_for("admin.user_list"))
    user.is_active_flag = not user.is_active_flag
    db.session.commit()
    flash(f"{user.username} is now {'active' if user.is_active_flag else 'disabled'}.", "info")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
def user_change_role(user_id: int):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    if new_role in (UserRole.USER.value, UserRole.ADMIN.value):
        user.role = UserRole(new_role)
        db.session.commit()
        flash(f"{user.username}'s role is now {new_role}.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def user_delete(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.user_list"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin.user_list"))


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@admin_bp.route("/analytics")
def analytics():
    from datetime import datetime, timedelta
    from sqlalchemy import func

    since = datetime.utcnow() - timedelta(days=30)

    registrations_by_day = (
        db.session.query(func.date(User.created_at), func.count(User.id))
        .filter(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )

    watch_by_day = (
        db.session.query(func.date(WatchHistory.last_watched), func.count(WatchHistory.id))
        .filter(WatchHistory.last_watched >= since)
        .group_by(func.date(WatchHistory.last_watched))
        .order_by(func.date(WatchHistory.last_watched))
        .all()
    )

    most_watched = Movie.query.order_by(Movie.view_count.desc()).limit(10).all()

    return render_template(
        "admin/analytics.html",
        registrations_by_day=[{"date": str(d), "count": c} for d, c in registrations_by_day],
        watch_by_day=[{"date": str(d), "count": c} for d, c in watch_by_day],
        most_watched=most_watched,
    )
