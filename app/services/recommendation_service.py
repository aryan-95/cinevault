"""
Recommendation service.

Implements a simple, explainable rule-based recommender today:

1. Look at the user's watch history and "My List" to find their most
   watched / saved genres.
2. Score every other movie by how many of those genres it shares,
   with a small boost for movies the user has rated highly in the past
   (via similar-genre affinity) and for globally trending titles.
3. Return the top-N unseen movies.

The public function signature (`get_recommendations_for_user`) is kept
deliberately stable so a future ML-based model (e.g. collaborative
filtering or a learned embedding model) can replace the internals
without touching any calling code in the routes.
"""

from __future__ import annotations

from collections import Counter

from app.models.movie import Movie
from app.models.watch_history import WatchHistory
from app.models.my_list import MyListEntry
from app.models.review import Review


def _genre_affinity(user_id: int) -> Counter:
    """Build a genre -> weight counter from a user's activity."""
    affinity: Counter = Counter()

    watched_movie_ids = [w.movie_id for w in WatchHistory.query.filter_by(user_id=user_id).all()]
    listed_movie_ids = [m.movie_id for m in MyListEntry.query.filter_by(user_id=user_id).all()]
    reviews = Review.query.filter_by(user_id=user_id).all()

    for movie_id in watched_movie_ids:
        movie = Movie.query.get(movie_id)
        if movie:
            for genre in movie.genre_list:
                affinity[genre] += 2

    for movie_id in listed_movie_ids:
        movie = Movie.query.get(movie_id)
        if movie:
            for genre in movie.genre_list:
                affinity[genre] += 1.5

    for review in reviews:
        movie = Movie.query.get(review.movie_id)
        if movie and review.rating >= 4:
            for genre in movie.genre_list:
                affinity[genre] += review.rating

    return affinity


def get_recommendations_for_user(user_id: int, limit: int = 12) -> list[Movie]:
    """Return up to `limit` recommended movies for a given user.

    Falls back to globally trending/popular movies when the user has
    no watch history yet (the classic "cold start" problem).
    """
    affinity = _genre_affinity(user_id)

    seen_movie_ids = {
        w.movie_id for w in WatchHistory.query.filter_by(user_id=user_id).all()
    }

    if not affinity:
        query = Movie.query.filter(~Movie.id.in_(seen_movie_ids)) if seen_movie_ids else Movie.query
        return (
            query.order_by(Movie.is_trending.desc(), Movie.view_count.desc())
            .limit(limit)
            .all()
        )

    candidates = Movie.query.filter(~Movie.id.in_(seen_movie_ids)).all() if seen_movie_ids else Movie.query.all()

    scored: list[tuple[float, Movie]] = []
    for movie in candidates:
        score = sum(affinity.get(genre, 0) for genre in movie.genre_list)
        if movie.is_trending:
            score += 1
        score += movie.average_rating * 0.5
        scored.append((score, movie))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [movie for score, movie in scored[:limit] if score > 0] or scored_fallback(candidates, limit)


def scored_fallback(candidates: list[Movie], limit: int) -> list[Movie]:
    """Fallback when nothing scores above zero: just return the newest movies."""
    return sorted(candidates, key=lambda m: m.created_at, reverse=True)[:limit]


def get_similar_movies(movie: Movie, limit: int = 8) -> list[Movie]:
    """Return movies sharing at least one genre with `movie`, excluding itself."""
    target_genres = set(movie.genre_list)
    if not target_genres:
        return Movie.query.filter(Movie.id != movie.id).limit(limit).all()

    others = Movie.query.filter(Movie.id != movie.id).all()
    scored = [
        (len(target_genres.intersection(other.genre_list)), other)
        for other in others
    ]
    scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [other for _, other in scored[:limit]]
