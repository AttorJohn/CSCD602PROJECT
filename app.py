"""
WasteTrack Ghana - Entry point.

Step 7 adds session-based authentication via Flask-Login: login,
logout, and the current_user available in every template
(implements FR-02).
"""
import os
from flask import Flask
from flask_login import LoginManager
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

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access that page."
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

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
