"""Authentication routes - registration (Step 6) and login/logout (Step 7).

Implements FR-01 (registration) and NFR-01 (passwords stored as
salted hashes, never plain text).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from models import db
from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if email and User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for message in errors:
                flash(message, "error")
            return render_template("register.html", name=name, email=email)

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="resident",
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. You can now log in.", "success")
        return redirect(url_for("home"))  # will point to auth.login once Step 7 is done

    return render_template("register.html", name="", email="")
