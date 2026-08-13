"""Tests for collection-request submission and validation (FR-04, FR-05, FR-06)."""
from io import BytesIO
import os


def _register_and_login(client, email="resident@example.com"):
    client.post(
        "/register",
        data={"name": "Resident", "email": email, "password": "password123"},
        follow_redirects=True,
    )
    client.post(
        "/login",
        data={"email": email, "password": "password123"},
        follow_redirects=True,
    )


def test_dashboard_requires_login(client):
    response = client.get("/dashboard/", follow_redirects=True)
    assert b"Log in" in response.data


def test_submit_request_missing_address_shows_error(client):
    _register_and_login(client)
    response = client.post(
        "/dashboard/new",
        data={"address": "", "waste_type": "household", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    assert b"Address is required" in response.data


def test_submit_request_past_date_rejected(client):
    _register_and_login(client)
    response = client.post(
        "/dashboard/new",
        data={"address": "12 Ring Rd", "waste_type": "household", "preferred_date": "2020-01-01", "description": ""},
        follow_redirects=True,
    )
    assert b"cannot be in the past" in response.data


def test_submit_request_invalid_waste_type_rejected(client):
    _register_and_login(client)
    response = client.post(
        "/dashboard/new",
        data={"address": "12 Ring Rd", "waste_type": "toxic_sludge", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    assert b"valid waste type" in response.data


def test_submit_valid_request_appears_on_dashboard(client):
    _register_and_login(client)
    response = client.post(
        "/dashboard/new",
        data={"address": "12 Ring Rd", "waste_type": "household", "preferred_date": "2027-01-01", "description": "Old sofa"},
        follow_redirects=True,
    )
    assert b"submitted successfully" in response.data
    assert b"#0001" in response.data
    assert b"Pending" in response.data


def test_request_photo_upload_is_saved_and_audited(client, app):
    _register_and_login(client)
    response = client.post(
        "/dashboard/new",
        data={
            "address": "12 Ring Rd", "waste_type": "household",
            "preferred_date": "2027-01-01", "description": "Old sofa",
            "photo": (BytesIO(b"\x89PNG\r\n\x1a\n"), "sofa.png", "image/png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"submitted successfully" in response.data
    assert b"View photo" in response.data

    with app.app_context():
        from models.audit import AuditLog
        from models.request import CollectionRequest
        collection_request = CollectionRequest.query.first()
        assert collection_request.photo_filename
        assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], collection_request.photo_filename))
        assert AuditLog.query.filter_by(action="Created collection request").count() == 1


def test_resident_cannot_see_another_residents_requests(client):
    _register_and_login(client, email="first@example.com")
    client.post(
        "/dashboard/new",
        data={"address": "Addr A", "waste_type": "household", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)

    _register_and_login(client, email="second@example.com")
    response = client.get("/dashboard/")
    assert b"#0001" not in response.data
    assert b"submitted any collection requests" in response.data


def test_resident_can_delete_their_account_and_request_history(client, app):
    _register_and_login(client, email="delete-me@example.com")
    client.post(
        "/dashboard/new",
        data={"address": "12 Ring Rd", "waste_type": "household", "preferred_date": "2027-01-01", "description": "Old sofa"},
        follow_redirects=True,
    )

    response = client.post(
        "/dashboard/account/delete",
        data={"password": "password123"},
        follow_redirects=True,
    )
    assert b"account and collection-request history have been deleted" in response.data

    with app.app_context():
        from models.request import CollectionRequest
        from models.user import User
        assert User.query.filter_by(email="delete-me@example.com").first() is None
        assert CollectionRequest.query.count() == 0


def test_account_deletion_requires_the_current_password(client, app):
    _register_and_login(client, email="keep-me@example.com")
    response = client.post(
        "/dashboard/account/delete",
        data={"password": "incorrect"},
        follow_redirects=True,
    )
    assert b"password was incorrect" in response.data

    with app.app_context():
        from models.user import User
        assert User.query.filter_by(email="keep-me@example.com").first() is not None


def test_resident_can_cancel_their_own_pending_request(client, app):
    _register_and_login(client)
    client.post(
        "/dashboard/new",
        data={"address": "12 Ring Rd", "waste_type": "household", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    response = client.post("/dashboard/requests/1/cancel", follow_redirects=True)
    assert b"has been cancelled" in response.data

    with app.app_context():
        from models import db
        from models.request import CollectionRequest
        assert db.session.get(CollectionRequest, 1).status == "cancelled"


def test_resident_cannot_cancel_another_residents_request(client):
    _register_and_login(client, email="first-cancel@example.com")
    client.post(
        "/dashboard/new",
        data={"address": "12 Ring Rd", "waste_type": "household", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)
    _register_and_login(client, email="second-cancel@example.com")
    response = client.post("/dashboard/requests/1/cancel")
    assert response.status_code == 404
