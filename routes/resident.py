"""Resident-facing routes - dashboard (Step 9) and request submission (Step 10).

Implements FR-04 (submit request), FR-05 (validate before saving),
FR-06 (view own requests) and FR-10 (resident dashboard).
"""
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, logout_user
from werkzeug.security import check_password_hash
from routes.decorators import resident_required
from models import db
from models.request import CollectionRequest, VALID_WASTE_TYPES

resident_bp = Blueprint("resident", __name__, url_prefix="/dashboard")


@resident_bp.route("/")
@resident_required
def dashboard():
    # Newest first - matches the "My Requests" list in the wireframe (Section 3.6)
    requests = (
        current_user.requests
        .order_by(CollectionRequest.created_at.desc())
        .all()
    )
    return render_template("dashboard.html", requests=requests)


@resident_bp.route("/new", methods=["GET", "POST"])
@resident_required
def new_request():
    if request.method == "POST":
        address = request.form.get("address", "").strip()
        waste_type = request.form.get("waste_type", "").strip().lower()
        preferred_date_raw = request.form.get("preferred_date", "").strip()
        description = request.form.get("description", "").strip()

        # FR-05: validate before anything is saved to the database
        errors = []
        if not address:
            errors.append("Address is required.")
        if waste_type not in VALID_WASTE_TYPES:
            errors.append("Please select a valid waste type.")

        preferred_date = None
        if not preferred_date_raw:
            errors.append("Preferred date is required.")
        else:
            try:
                preferred_date = datetime.strptime(preferred_date_raw, "%Y-%m-%d").date()
                if preferred_date < date.today():
                    errors.append("Preferred date cannot be in the past.")
            except ValueError:
                errors.append("Preferred date is not a valid date.")

        if errors:
            for message in errors:
                flash(message, "error")
            return render_template(
                "new_request.html",
                waste_types=VALID_WASTE_TYPES,
                address=address,
                waste_type=waste_type,
                preferred_date=preferred_date_raw,
                description=description,
            )

        new_req = CollectionRequest(
            user_id=current_user.id,
            address=address,
            waste_type=waste_type,
            description=description or None,
            preferred_date=preferred_date,
            status="pending",
        )
        db.session.add(new_req)
        db.session.commit()

        flash(f"Request #{new_req.id:04d} submitted successfully.", "success")
        return redirect(url_for("resident.dashboard"))

    return render_template(
        "new_request.html",
        waste_types=VALID_WASTE_TYPES,
        address="",
        waste_type="",
        preferred_date="",
        description="",
    )


@resident_bp.route("/account/delete", methods=["POST"])
@resident_required
def delete_account():
    """Permanently remove a resident and their request history."""
    password = request.form.get("password", "")
    if not check_password_hash(current_user.password_hash, password):
        flash("Your password was incorrect. Your account was not deleted.", "error")
        return redirect(url_for("resident.dashboard"))

    # Requests belong to the resident, so remove them before the account to
    # preserve foreign-key integrity and honour the permanent-delete warning.
    user = current_user._get_current_object()
    for collection_request in user.requests.all():
        db.session.delete(collection_request)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    flash("Your account and collection-request history have been deleted.", "success")
    return redirect(url_for("home"))
