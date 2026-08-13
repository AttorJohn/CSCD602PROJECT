"""Tests for registration and login/logout (FR-01, FR-02, NFR-01)."""


def test_register_creates_user_with_hashed_password(client, app):
    from models.user import User

    response = client.post(
        "/register",
        data={"name": "Ama Mensah", "email": "ama@example.com", "password": "secret123"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="ama@example.com").first()
        assert user is not None
        assert user.password_hash != "secret123"  # NFR-01: never stored plain
        assert user.role == "resident"


def test_cannot_register_duplicate_email(client):
    data = {"name": "Ama", "email": "dupe@example.com", "password": "secret123"}
    client.post("/register", data=data, follow_redirects=True)
    response = client.post("/register", data=data, follow_redirects=True)
    assert b"already exists" in response.data


def test_login_with_wrong_password_fails(client):
    client.post(
        "/register",
        data={"name": "Kojo", "email": "kojo@example.com", "password": "correctpw"},
        follow_redirects=True,
    )
    response = client.post(
        "/login",
        data={"email": "kojo@example.com", "password": "wrongpw"},
        follow_redirects=True,
    )
    assert b"Invalid email or password" in response.data


def test_login_redirects_resident_to_dashboard(client):
    client.post(
        "/register",
        data={"name": "Yaw", "email": "yaw@example.com", "password": "correctpw"},
        follow_redirects=True,
    )
    response = client.post(
        "/login",
        data={"email": "yaw@example.com", "password": "correctpw"},
        follow_redirects=True,
    )
    assert b"My Requests" in response.data  # dashboard content


def test_logout_without_login_redirects_to_login_page(client):
    response = client.post("/logout", follow_redirects=True)
    assert b"Log in" in response.data
