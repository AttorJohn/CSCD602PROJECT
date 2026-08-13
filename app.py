"""
WasteTrack Ghana - Entry point.

Step 8 adds role-based authorisation (FR-03, NFR-03). Administrators
are never created through the public /register form - only through
the `flask create-admin` CLI command below - so nobody can grant
themselves admin access through the UI.
"""
import os
import click
from flask import Flask
from flask_login import LoginManager
from models import db
from routes.auth import auth_bp
from routes.decorators import admin_required, resident_required

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

    # --- Temporary verification routes for Step 8 only.
    # Replaced by the real resident dashboard (Step 10) and admin
    # dashboard (Step 11-12).
    @app.route("/resident/ping")
    @resident_required
    def resident_ping():
        return "Resident access confirmed."

    @app.route("/admin/ping")
    @admin_required
    def admin_ping():
        return "Admin access confirmed."

    # --- CLI command to create/promote an admin account.
    # Run from the terminal (app must NOT be running at the same time):
    #   flask --app app create-admin "Admin Name" admin@example.com somepassword
    @app.cli.command("create-admin")
    @click.argument("name")
    @click.argument("email")
    @click.argument("password")
    def create_admin(name, email, password):
        """Create a new admin user, or promote an existing user to admin."""
        from models.user import User
        from werkzeug.security import generate_password_hash

        email = email.strip().lower()
        with app.app_context():
            user = User.query.filter_by(email=email).first()
            if user:
                user.role = "admin"
                db.session.commit()
                click.echo(f"Promoted existing user {email} to admin.")
                return

            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role="admin",
            )
            db.session.add(user)
            db.session.commit()
            click.echo(f"Created admin user {email}.")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
