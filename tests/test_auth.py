"""Tests for registration, login, logout, and profile management."""
from app.models.user import User
from tests.conftest import login


def test_register_creates_user(client, db):
    response = client.post(
        "/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "confirm_password": "securepass123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert User.query.filter_by(email="newuser@example.com").first() is not None


def test_register_rejects_mismatched_passwords(client, db):
    client.post(
        "/register",
        data={
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password": "securepass123",
            "confirm_password": "different123",
        },
        follow_redirects=True,
    )
    assert User.query.filter_by(email="mismatch@example.com").first() is None


def test_register_rejects_duplicate_email(client, db, sample_user):
    response = client.post(
        "/register",
        data={
            "username": "someoneelse",
            "email": sample_user.email,
            "password": "securepass123",
            "confirm_password": "securepass123",
        },
        follow_redirects=True,
    )
    assert b"already exists" in response.data or response.status_code == 200
    assert User.query.filter_by(email=sample_user.email).count() == 1


def test_login_success(client, sample_user):
    response = login(client, "test@example.com", "password123")
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "_user_id" in sess


def test_login_wrong_password_fails(client, sample_user):
    response = login(client, "test@example.com", "wrongpassword")
    with client.session_transaction() as sess:
        assert "_user_id" not in sess


def test_logout_clears_session(client, sample_user):
    login(client, "test@example.com", "password123")
    client.get("/logout")
    with client.session_transaction() as sess:
        assert "_user_id" not in sess


def test_password_hash_is_not_plaintext(sample_user):
    assert sample_user.password_hash != "password123"
    assert sample_user.check_password("password123")
    assert not sample_user.check_password("wrongpassword")


def test_change_password(client, db, sample_user):
    login(client, "test@example.com", "password123")
    client.post(
        "/profile",
        data={
            "action": "change_password",
            "current_password": "password123",
            "new_password": "newpassword456",
            "confirm_new_password": "newpassword456",
        },
        follow_redirects=True,
    )
    db.session.refresh(sample_user)
    assert sample_user.check_password("newpassword456")


def test_delete_account(client, db, sample_user):
    login(client, "test@example.com", "password123")
    client.post("/profile", data={"action": "delete_account"}, follow_redirects=True)
    assert User.query.filter_by(email="test@example.com").first() is None
