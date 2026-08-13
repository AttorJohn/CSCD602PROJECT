"""
WasteTrack Ghana - Entry point.

Step 6 adds registration via the auth blueprint (routes/auth.py),
implementing FR-01 and NFR-01 (passwords hashed, never stored plain).
"""
import os
from flask import Flask
from models import db
from routes.auth import auth_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = "dev-only-change-me"  # TODO: move to env var before deployment
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + os.path.join(app.instance_path, "wastetrack.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()  # creates users/requests/collectors tables if they don't exist yet

    app.register_blueprint(auth_bp)

    @app.route("/")
    def home():
        return "Hello, WasteTrack Ghana! The Flask app is running."

    @app.route("/db-check")
    def db_check():
        from models.user import User
        count = User.query.count()
        return f"Database connected. Users table has {count} row(s)."

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
