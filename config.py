import os
import secrets
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # A configured key keeps sessions valid across restarts. A random fallback
    # is safe for local development, but deliberately invalidates sessions when
    # the server restarts, making a missing production setting obvious.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(basedir, "instance", "wastetrack.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CSRF_ENABLED = True
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit
