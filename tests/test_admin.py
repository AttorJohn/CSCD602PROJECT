"""Tests for the admin dashboard, role-based access, collector
assignment and status transitions (FR-03, FR-07, FR-08, FR-09, NFR-03).
"""


def _make_admin(app, email="admin@example.com", password="adminpass1"):
    from models.user import User
    from models import db
    from werkzeug.security import generate_password_hash

    with app.app_context():
        admin = User(
            name="Admin User",
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()


def _register_resident(client, email="resident@example.com"):
    client.post(
        "/register",
        data={"name": "Resident", "email": email, "password": "password123"},
        follow_redirects=True,
    )


def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_resident_cannot_reach_admin_dashboard(client):
    _register_resident(client)
    _login(client, "resident@example.com", "password123")
    response = client.get("/admin/")
    assert response.status_code == 403  # NFR-03: server-side block, not just a hidden link


def test_anonymous_user_redirected_to_login(client):
    response = client.get("/admin/", follow_redirects=True)
    assert b"Log in" in response.data


def test_admin_can_assign_collector_to_pending_request(client, app):
    _make_admin(app)
    _register_resident(client, email="resident2@example.com")
    _login(client, "resident2@example.com", "password123")
    client.post(
        "/dashboard/new",
        data={"address": "Addr B", "waste_type": "household", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)

    _login(client, "admin@example.com", "adminpass1")
    client.post(
        "/admin/collectors/new",
        data={"name": "Kofi Mensah", "phone": "0551234567"},
        follow_redirects=True,
    )

    with app.app_context():
        from models.request import CollectionRequest
        from models.collector import Collector
        req_id = CollectionRequest.query.first().id
        collector_id = Collector.query.first().id

    response = client.post(
        f"/admin/requests/{req_id}/assign",
        data={"collector_id": collector_id},
        follow_redirects=True,
    )
    assert b"assigned to Kofi Mensah" in response.data

    with app.app_context():
        from models import db
        from models.collector import Collector
        from models.request import CollectionRequest
        updated = db.session.get(CollectionRequest, req_id)
        assert updated.status == "assigned"
        assert updated.collector_id == collector_id
        assert db.session.get(Collector, collector_id).status == "busy"

    response = client.post(
        f"/admin/requests/{req_id}/status",
        data={"new_status": "in_progress"},
        follow_redirects=True,
    )
    assert b"status updated to In Progress" in response.data
    response = client.post(
        f"/admin/requests/{req_id}/status",
        data={"new_status": "collected"},
        follow_redirects=True,
    )
    assert b"status updated to Collected" in response.data

    with app.app_context():
        from models import db
        from models.collector import Collector
        assert db.session.get(Collector, collector_id).status == "available"
        from models.audit import AuditLog
        assert AuditLog.query.filter_by(action="Assigned collector").count() == 1
        assert AuditLog.query.filter_by(action="Updated request status").count() == 2


def test_invalid_status_transition_rejected(client, app):
    _make_admin(app)
    _register_resident(client, email="resident3@example.com")
    _login(client, "resident3@example.com", "password123")
    client.post(
        "/dashboard/new",
        data={"address": "Addr C", "waste_type": "household", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)

    _login(client, "admin@example.com", "adminpass1")

    with app.app_context():
        from models.request import CollectionRequest
        req_id = CollectionRequest.query.first().id

    # Request is still "pending" - jumping straight to "collected" skips
    # the state machine (Section 3.4) and must be rejected.
    response = client.post(
        f"/admin/requests/{req_id}/status",
        data={"new_status": "collected"},
        follow_redirects=True,
    )
    assert b"Cannot move request" in response.data

    with app.app_context():
        from models import db
        from models.request import CollectionRequest
        unchanged = db.session.get(CollectionRequest, req_id)
        assert unchanged.status == "pending"


def test_admin_can_filter_requests_and_see_status_statistics(client, app):
    _make_admin(app)
    with app.app_context():
        from datetime import date
        from models import db
        from models.request import CollectionRequest
        from models.user import User

        resident = User(
            name="Dashboard Resident",
            email="dashboard@example.com",
            password_hash="not-used",
            role="resident",
        )
        db.session.add(resident)
        db.session.flush()
        db.session.add_all([
            CollectionRequest(user_id=resident.id, address="Pending address", waste_type="household", preferred_date=date(2027, 1, 1), status="pending"),
            CollectionRequest(user_id=resident.id, address="Assigned address", waste_type="household", preferred_date=date(2027, 1, 1), status="assigned"),
            CollectionRequest(user_id=resident.id, address="Collected address", waste_type="household", preferred_date=date(2027, 1, 1), status="collected"),
        ])
        db.session.commit()

    _login(client, "admin@example.com", "adminpass1")
    response = client.get("/admin/?status=pending")
    assert b'data-request-status="pending"' in response.data
    assert b'data-request-status="assigned"' not in response.data
    assert b'data-request-status="collected"' not in response.data
    assert b">1</span>" in response.data
