"""Tests for admin authorization and JSON REST API endpoints."""
import json

from tests.conftest import login


def test_admin_dashboard_blocked_for_anonymous(client):
    response = client.get("/admin/")
    assert response.status_code in (302, 403)


def test_admin_dashboard_blocked_for_regular_user(client, sample_user):
    login(client, "test@example.com", "password123")
    response = client.get("/admin/")
    assert response.status_code == 403


def test_admin_dashboard_accessible_for_admin(client, admin_user):
    login(client, "admin@example.com", "adminpassword123")
    response = client.get("/admin/")
    assert response.status_code == 200


def test_admin_can_create_movie_via_ui(client, db, admin_user):
    login(client, "admin@example.com", "adminpassword123")
    response = client.post(
        "/admin/movies/new",
        data={
            "title": "Admin Created Movie",
            "description": "Created via admin form.",
            "release_year": "2024",
            "duration_minutes": "100",
            "genre": "Drama",
            "language": "English",
            "age_rating": "PG-13",
            "cast": "",
            "director": "",
            "trailer_url": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Admin Created Movie" in response.data


def test_regular_user_cannot_delete_movie(client, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    response = client.post(f"/admin/movies/{sample_movie.id}/delete", follow_redirects=True)
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_api_register_and_login(client, db):
    response = client.post(
        "/api/auth/register",
        json={"username": "apiuser", "email": "apiuser@example.com", "password": "apipassword123"},
    )
    assert response.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={"identifier": "apiuser@example.com", "password": "apipassword123"},
    )
    assert response.status_code == 200


def test_api_list_movies(client, sample_movie):
    response = client.get("/api/movies")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] >= 1


def test_api_get_movie(client, sample_movie):
    response = client.get(f"/api/movies/{sample_movie.id}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["title"] == "Test Movie"


def test_api_create_movie_requires_admin(client, sample_user):
    login(client, "test@example.com", "password123")
    response = client.post("/api/movies", json={"title": "Should Fail"})
    assert response.status_code == 403


def test_api_create_movie_as_admin(client, admin_user):
    login(client, "admin@example.com", "adminpassword123")
    response = client.post("/api/movies", json={"title": "API Movie", "release_year": 2024})
    assert response.status_code == 201


def test_api_search(client, sample_movie):
    response = client.get("/api/search?q=Test")
    data = json.loads(response.data)
    assert len(data["results"]) >= 1


def test_api_my_list_flow(client, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    response = client.post(f"/api/my-list/{sample_movie.id}")
    assert response.status_code == 201

    response = client.get("/api/my-list")
    data = json.loads(response.data)
    assert any(m["id"] == sample_movie.id for m in data["movies"])

    response = client.delete(f"/api/my-list/{sample_movie.id}")
    assert response.status_code == 200


def test_api_watch_progress(client, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    response = client.post(
        "/api/watch-progress",
        json={"movie_id": sample_movie.id, "progress_seconds": 300, "duration_seconds": 6000},
    )
    assert response.status_code == 200


def test_api_review_lifecycle(client, sample_user, sample_movie):
    login(client, "test@example.com", "password123")
    response = client.post(
        "/api/reviews", json={"movie_id": sample_movie.id, "rating": 4, "review_text": "Nice"}
    )
    assert response.status_code == 201
    review_id = json.loads(response.data)["id"]

    response = client.put(f"/api/reviews/{review_id}", json={"rating": 5})
    assert response.status_code == 200

    response = client.delete(f"/api/reviews/{review_id}")
    assert response.status_code == 200
