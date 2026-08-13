"""Shared pytest fixtures.

Every test gets a fresh app wired to an in-memory SQLite database
(via create_app's test_config hook), so tests never touch the real
instance/wastetrack.db file and never leak state between tests.
"""
import pytest
from app import create_app


@pytest.fixture
def app():
    flask_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
    })
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
