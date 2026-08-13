"""Tests for collection-request submission and validation (FR-04, FR-05, FR-06)."""


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


def test_resident_cannot_see_another_residents_requests(client):
    _register_and_login(client, email="first@example.com")
    client.post(
        "/dashboard/new",
        data={"address": "Addr A", "waste_type": "household", "preferred_date": "2027-01-01", "description": ""},
        follow_redirects=True,
    )
    client.get("/logout", follow_redirects=True)

    _register_and_login(client, email="second@example.com")
    response = client.get("/dashboard/")
    assert b"#0001" not in response.data
    assert b"submitted any collection requests" in response.data
