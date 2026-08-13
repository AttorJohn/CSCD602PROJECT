"""
WasteTrack Ghana - Entry point.

Steps 11-15 in one pass:
- Step 11: admin dashboard (replaces the /admin/ping stub)
- Step 12: collector assignment / status changes (routes/admin.py)
- Step 13: custom 403/404/500 error pages
- Step 14: UI refinement (see templates/static, not this file)
- Step 15: create_app(test_config) hook so pytest can run against an
  in-memory database instead of the real SQLite file
"""
import secrets

import click
from flask import Flask, abort, render_template, request, session
from flask_login import LoginManager
from config import Config
from models import db
from routes.auth import auth_bp
from routes.resident import resident_bp
from routes.admin import admin_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        # Lets tests/conftest.py swap in an in-memory database etc.
        # BEFORE db.init_app()/create_all() bind to the real file.
        app.config.update(test_config)

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
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_csrf_token():
        def csrf_token():
            if "csrf_token" not in session:
                session["csrf_token"] = secrets.token_urlsafe(32)
            return session["csrf_token"]
        return {"csrf_token": csrf_token}

    @app.before_request
    def protect_against_csrf():
        if app.config["CSRF_ENABLED"] and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            submitted_token = request.form.get("csrf_token", "")
            if not submitted_token or submitted_token != session.get("csrf_token"):
                abort(400)

    app.register_blueprint(auth_bp)
    app.register_blueprint(resident_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return render_template("home.html")

    # --- Step 13: custom error pages instead of raw Flask/Werkzeug defaults.
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template(
            "error.html", code=403, title="Forbidden",
            message="You don't have permission to view this page.",
        ), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template(
            "error.html", code=404, title="Page Not Found",
            message="That page doesn't exist.",
        ), 404

    @app.errorhandler(400)
    def bad_request(_e):
        return render_template(
            "error.html", code=400, title="Invalid Request",
            message="Your form could not be verified. Please try again.",
        ), 400

    @app.errorhandler(500)
    def server_error(_e):
        return render_template(
            "error.html", code=500, title="Something Went Wrong",
            message="An unexpected error occurred. Please try again.",
        ), 500

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
    app.run(debug=app.config["DEBUG"])
