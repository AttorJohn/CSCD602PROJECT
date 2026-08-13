"""Authentication routes - registration (Step 6) and login/logout (Step 7).

Implements FR-01 (registration), FR-02 (login/logout) and NFR-01
(passwords stored as salted hashes, never plain text).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
from models.user import User
from models.collector import Collector
from models.audit import record_audit

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@auth_bp.route("/register/resident", methods=["GET", "POST"])
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
            return render_template("register.html", name=name, email=email, portal="resident")

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="resident",
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login", portal="resident"))

    return render_template("register.html", name="", email="", portal="resident")


@auth_bp.route("/register/collector", methods=["GET", "POST"])
def register_collector():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not phone:
            errors.append("Phone number is required for collectors.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if email and User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")
        if errors:
            for message in errors:
                flash(message, "error")
            return render_template("register.html", name=name, email=email, phone=phone, portal="collector")

        user = User(name=name, email=email, password_hash=generate_password_hash(password), role="collector")
        db.session.add(user)
        db.session.flush()
        db.session.add(Collector(user_id=user.id, name=name, phone=phone, status="available"))
        record_audit(user, "Registered collector profile", details=phone)
        db.session.commit()
        flash("Collector account created. Please log in.", "success")
        return redirect(url_for("auth.login", portal="collector"))

    return render_template("register.html", name="", email="", phone="", portal="collector")


@auth_bp.route("/login", methods=["GET", "POST"])
@auth_bp.route("/login/<portal>", methods=["GET", "POST"])
def login(portal=None):
    if portal not in {None, "resident", "collector", "admin"}:
        portal = None
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password) and (portal is None or user.role == portal):
            login_user(user)
            flash(f"Welcome back, {user.name}.", "success")
            if user.role == "resident":
                return redirect(url_for("resident.dashboard"))
            if user.role == "collector":
                return redirect(url_for("collector.dashboard"))
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")
        return render_template("login.html", email=email, portal=portal)

    return render_template("login.html", email="", portal=portal)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))
