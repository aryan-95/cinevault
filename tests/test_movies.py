"""Tests for movie listing, detail pages, search, My List, and watch progress."""
from app.models.my_list import MyListEntry
from app.models.watch_history import WatchHistory
from app.models.review import Review
from tests.conftest import login


def test_homepage_loads(client, sample_movie):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Test Movie" in response.data


def test_movie_detail_page(client, sample_movie):
    response = client.get(f"/movie/{sample_movie.id}")
    assert response.status_code == 200
    assert b"Test Movie" in response.data


def test_movie_detail_404_for_missing_movie(client):
    response = client.get("/movie/99999")
    assert response.status_code == 404


def test_search_by_title(client, sample_movie):
    response = client.get("/search?q=Test Movie")
    assert response.status_code == 200
    assert b"Test Movie" in response.data


def test_search_no_results(client, sample_movie):
    response = client.get("/search?q=NoSuchMovieTitleXYZ")
    assert response.status_code == 200
    assert b"Test Movie" not in response.data


def test_genre_page(client, sample_movie):
    response = client.get("/genre/Action")
    assert response.status_code == 200
    assert b"Test Movie" in response.data


def test_watch_requires_login(client, sample_movie):
    response = client.get(f"/watch/{sample_movie.id}", follow_redirects=True)
    assert b"log in" in response.data.lower() or response.status_code == 200


def test_watch_page_for_logged_in_user(client, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    response = client.get(f"/watch/{sample_movie.id}")
    assert response.status_code == 200


def test_add_and_view_my_list(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(f"/my-list/{sample_movie.id}/add", follow_redirects=True)
    assert MyListEntry.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).first() is not None

    response = client.get("/my-list")
    assert b"Test Movie" in response.data


def test_my_list_prevents_duplicates(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(f"/my-list/{sample_movie.id}/add", follow_redirects=True)
    client.post(f"/my-list/{sample_movie.id}/add", follow_redirects=True)
    count = MyListEntry.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).count()
    assert count == 1


def test_remove_from_my_list(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(f"/my-list/{sample_movie.id}/add", follow_redirects=True)
    client.post(f"/my-list/{sample_movie.id}/remove", follow_redirects=True)
    assert MyListEntry.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).first() is None


def test_watch_progress_is_saved(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(
        f"/watch/{sample_movie.id}/progress",
        json={"progress_seconds": 1200, "duration_seconds": 6000},
    )
    entry = WatchHistory.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).first()
    assert entry is not None
    assert entry.progress_seconds == 1200
    assert entry.completed is False


def test_watch_progress_marks_completed_near_end(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(
        f"/watch/{sample_movie.id}/progress",
        json={"progress_seconds": 5900, "duration_seconds": 6000},
    )
    entry = WatchHistory.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).first()
    assert entry.completed is True


def test_submit_review(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(
        f"/movie/{sample_movie.id}/review",
        data={"rating": "5", "review_text": "Great movie!"},
        follow_redirects=True,
    )
    review = Review.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).first()
    assert review is not None
    assert review.rating == 5


def test_cannot_submit_duplicate_review_rows(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(f"/movie/{sample_movie.id}/review", data={"rating": "4", "review_text": "Good"})
    client.post(f"/movie/{sample_movie.id}/review", data={"rating": "5", "review_text": "Even better"})
    count = Review.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).count()
    assert count == 1


def test_delete_review(client, db, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    client.post(f"/movie/{sample_movie.id}/review", data={"rating": "4", "review_text": "Good"})
    client.post(f"/movie/{sample_movie.id}/review/delete", follow_redirects=True)
    assert Review.query.filter_by(user_id=sample_user.id, movie_id=sample_movie.id).first() is None
