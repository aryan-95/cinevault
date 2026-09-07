"""Movie detail page, video player page, reviews, and My List actions."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import csrf, db
from app.models.movie import Movie
from app.models.my_list import MyListEntry
from app.models.review import Review
from app.models.watch_history import WatchHistory
from app.services.recommendation_service import get_similar_movies
from app.services.video_service import resolve_stream_url

movies_bp = Blueprint("movies", __name__)


@movies_bp.route("/movie/<int:movie_id>")
def detail(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    similar_movies = get_similar_movies(movie, limit=8)

    in_my_list = False
    user_review = None
    if current_user.is_authenticated:
        in_my_list = MyListEntry.query.filter_by(
            user_id=current_user.id, movie_id=movie.id
        ).first() is not None
        user_review = Review.query.filter_by(
            user_id=current_user.id, movie_id=movie.id
        ).first()

    reviews = (
        Review.query.filter_by(movie_id=movie.id)
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "movie.html",
        movie=movie,
        similar_movies=similar_movies,
        in_my_list=in_my_list,
        user_review=user_review,
        reviews=reviews,
    )


@movies_bp.route("/watch/<int:movie_id>")
@login_required
def watch(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    movie.view_count += 1
    db.session.commit()

    stream_url, media_type = resolve_stream_url(movie)

    history = WatchHistory.query.filter_by(
        user_id=current_user.id, movie_id=movie.id
    ).first()
    resume_at = history.progress_seconds if history and not history.completed else 0

    return render_template(
        "watch.html",
        movie=movie,
        stream_url=stream_url,
        media_type=media_type,
        resume_at=resume_at,
    )


@movies_bp.route("/watch/<int:movie_id>/progress", methods=["POST"])
@csrf.exempt
@login_required
def update_progress(movie_id: int):
    """AJAX endpoint the player calls periodically to persist playback position."""
    movie = Movie.query.get_or_404(movie_id)
    data = request.get_json(silent=True) or request.form

    try:
        progress_seconds = int(float(data.get("progress_seconds", 0)))
        duration_seconds = int(float(data.get("duration_seconds", 0)))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid progress payload."}), 400

    history = WatchHistory.query.filter_by(
        user_id=current_user.id, movie_id=movie.id
    ).first()
    if not history:
        history = WatchHistory(user_id=current_user.id, movie_id=movie.id)
        db.session.add(history)

    history.progress_seconds = max(progress_seconds, 0)
    history.duration_seconds = max(duration_seconds, history.duration_seconds or 0)
    history.last_watched = datetime.utcnow()
    if history.duration_seconds and history.progress_seconds >= history.duration_seconds * 0.95:
        history.completed = True

    db.session.commit()
    return jsonify({"status": "ok", "completion_percentage": history.completion_percentage})


@movies_bp.route("/my-list/<int:movie_id>/add", methods=["POST"])
@login_required
def add_to_list(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    existing = MyListEntry.query.filter_by(user_id=current_user.id, movie_id=movie.id).first()
    if not existing:
        db.session.add(MyListEntry(user_id=current_user.id, movie_id=movie.id))
        db.session.commit()

    if request.is_json:
        return jsonify({"status": "added"})
    flash(f"Added \"{movie.title}\" to My List.", "success")
    return redirect(request.referrer or url_for("movies.detail", movie_id=movie.id))


@movies_bp.route("/my-list/<int:movie_id>/remove", methods=["POST"])
@login_required
def remove_from_list(movie_id: int):
    entry = MyListEntry.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()

    if request.is_json:
        return jsonify({"status": "removed"})
    flash("Removed from My List.", "info")
    return redirect(request.referrer or url_for("main.my_list"))


@movies_bp.route("/movie/<int:movie_id>/review", methods=["POST"])
@login_required
def submit_review(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)

    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0

    review_text = request.form.get("review_text", "").strip()

    if rating < 1 or rating > 5:
        flash("Please select a rating between 1 and 5 stars.", "danger")
        return redirect(url_for("movies.detail", movie_id=movie.id))

    existing = Review.query.filter_by(user_id=current_user.id, movie_id=movie.id).first()
    if existing:
        existing.rating = rating
        existing.review_text = review_text
        existing.updated_at = datetime.utcnow()
        flash("Your review has been updated.", "success")
    else:
        db.session.add(
            Review(user_id=current_user.id, movie_id=movie.id, rating=rating, review_text=review_text)
        )
        flash("Thanks for your review!", "success")

    db.session.commit()
    return redirect(url_for("movies.detail", movie_id=movie.id))


@movies_bp.route("/movie/<int:movie_id>/review/delete", methods=["POST"])
@login_required
def delete_review(movie_id: int):
    review = Review.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if review:
        db.session.delete(review)
        db.session.commit()
        flash("Your review has been deleted.", "info")
    return redirect(url_for("movies.detail", movie_id=movie_id))
