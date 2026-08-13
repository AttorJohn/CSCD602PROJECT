"""Resident-facing routes - dashboard (Step 9) and request submission (Step 10).

Implements FR-04 (submit request), FR-05 (validate before saving),
FR-06 (view own requests) and FR-10 (resident dashboard).
"""
import os
import uuid
from datetime import date, datetime
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import current_user, logout_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from routes.decorators import resident_required
from models import db
from models.request import CollectionRequest, VALID_WASTE_TYPES
from models.audit import record_audit

resident_bp = Blueprint("resident", __name__, url_prefix="/dashboard")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def save_request_photo(photo):
    """Validate and store a request image under a generated server-side name."""
    if not photo or not photo.filename:
        return None, None

    safe_name = secure_filename(photo.filename)
    extension = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS or not photo.mimetype.startswith("image/"):
        return None, "Please upload a JPG, PNG, or WebP image."

    stored_name = f"{uuid.uuid4().hex}.{extension}"
    photo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name))
    return stored_name, None


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
        photo = request.files.get("photo")

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

        photo_filename, photo_error = save_request_photo(photo)
        if photo_error:
            flash(photo_error, "error")
            return render_template(
                "new_request.html", waste_types=VALID_WASTE_TYPES, address=address,
                waste_type=waste_type, preferred_date=preferred_date_raw, description=description,
            )

        new_req = CollectionRequest(
            user_id=current_user.id,
            address=address,
            waste_type=waste_type,
            description=description or None,
            photo_filename=photo_filename,
            preferred_date=preferred_date,
            status="pending",
        )
        db.session.add(new_req)
        db.session.flush()
        record_audit(current_user, "Created collection request", new_req.id)
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


@resident_bp.route("/requests/<int:request_id>/cancel", methods=["POST"])
@resident_required
def cancel_request(request_id):
    """Let a resident cancel only their own pending request."""
    collection_request = CollectionRequest.query.filter_by(
        id=request_id, user_id=current_user.id
    ).first_or_404()

    if collection_request.status != "pending":
        flash("Only pending collection requests can be cancelled.", "error")
        return redirect(url_for("resident.dashboard"))

    collection_request.status = "cancelled"
    record_audit(current_user, "Cancelled collection request", collection_request.id)
    db.session.commit()
    flash(f"Request #{collection_request.id:04d} has been cancelled.", "success")
    return redirect(url_for("resident.dashboard"))


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
    record_audit(user, "Deleted resident account", details=f"Deleted account for {user.email}")
    for collection_request in user.requests.all():
        if collection_request.photo_filename:
            photo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], collection_request.photo_filename)
            if os.path.isfile(photo_path):
                os.remove(photo_path)
        db.session.delete(collection_request)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    flash("Your account and collection-request history have been deleted.", "success")
    return redirect(url_for("home"))
