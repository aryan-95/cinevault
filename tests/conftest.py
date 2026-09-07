"""Shared pytest fixtures for the CineVault test suite."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app, db as _db
from app.models.user import User, UserRole
from app.models.movie import Movie


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def sample_user(app, db):
    user = User(username="testuser", email="test@example.com", role=UserRole.USER)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def admin_user(app, db):
    admin = User(username="testadmin", email="admin@example.com", role=UserRole.ADMIN)
    admin.set_password("adminpassword123")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture()
def sample_movie(app, db):
    movie = Movie(
        title="Test Movie",
        description="A movie used for testing.",
        release_year=2023,
        duration_minutes=100,
        genre="Action,Sci-Fi",
        language="English",
        cast="Test Actor",
        director="Test Director",
        poster_url="/media/posters/test.jpg",
        backdrop_url="/media/backdrops/test.jpg",
        video_url="/media/movies/test.mp4",
    )
    db.session.add(movie)
    db.session.commit()
    return movie


def login(client, identifier: str, password: str):
    return client.post(
        "/login",
        data={"identifier": identifier, "password": password},
        follow_redirects=True,
    )
