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
import os
import click
from flask import Flask, render_template
from flask_login import LoginManager
from models import db
from routes.auth import auth_bp
from routes.resident import resident_bp
from routes.admin import admin_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = "dev-only-change-me"  # TODO: move to env var before deployment
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + os.path.join(app.instance_path, "wastetrack.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        # Lets tests/conftest.py swap in an in-memory database etc.
        # BEFORE db.init_app()/create_all() bind to the real file.
        app.config.update(test_config)

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
    app.register_blueprint(resident_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/db-check")
    def db_check():
        from models.user import User
        count = User.query.count()
        return f"Database connected. Users table has {count} row(s)."

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
    app.run(debug=True)
