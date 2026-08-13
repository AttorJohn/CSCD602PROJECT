"""Tests for self-registering collector accounts and assigned-work access."""


def _register_collector(client, email="collector@example.com"):
    return client.post(
        "/register/collector",
        data={"name": "Kofi Collector", "email": email, "phone": "0551234567", "password": "collect123"},
        follow_redirects=True,
    )


def test_collector_can_register_with_profile_and_login(client, app):
    response = _register_collector(client)
    assert b"Collector account created" in response.data

    with app.app_context():
        from models.collector import Collector
        collector = Collector.query.first()
        assert collector.phone == "0551234567"
        assert collector.user.role == "collector"

    response = client.post(
        "/login/collector",
        data={"email": "collector@example.com", "password": "collect123"},
        follow_redirects=True,
    )
    assert b"My assigned collections" in response.data


def test_collector_can_progress_only_their_assigned_request(client, app):
    _register_collector(client)
    client.post(
        "/login/collector",
        data={"email": "collector@example.com", "password": "collect123"},
        follow_redirects=True,
    )
    with app.app_context():
        from datetime import date
        from werkzeug.security import generate_password_hash
        from models import db
        from models.collector import Collector
        from models.request import CollectionRequest
        from models.user import User

        resident = User(name="Resident", email="assigned@example.com", password_hash=generate_password_hash("password123"), role="resident")
        db.session.add(resident)
        db.session.flush()
        collector = Collector.query.first()
        collection_request = CollectionRequest(
            user_id=resident.id, collector_id=collector.id, address="Assigned address",
            waste_type="household", preferred_date=date(2027, 1, 1), status="assigned",
        )
        collector.status = "busy"
        db.session.add(collection_request)
        db.session.commit()
        request_id = collection_request.id

    response = client.post(
        f"/collector/requests/{request_id}/status", data={"new_status": "in_progress"}, follow_redirects=True
    )
    assert b"updated to In Progress" in response.data

    with app.app_context():
        from models import db
        from models.request import CollectionRequest
        assert db.session.get(CollectionRequest, request_id).status == "in_progress"


def test_collector_portal_rejects_resident_login(client):
    client.post(
        "/register",
        data={"name": "Resident", "email": "resident-portal@example.com", "password": "password123"},
        follow_redirects=True,
    )
    response = client.post(
        "/login/collector",
        data={"email": "resident-portal@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert b"Invalid email or password" in response.data
