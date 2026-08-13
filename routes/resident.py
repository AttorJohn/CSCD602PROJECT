"""Resident-facing routes - dashboard (Step 9) and request submission (Step 10).

Implements FR-06 (view own requests) and FR-10 (resident dashboard).
"""
from flask import Blueprint, render_template
from flask_login import current_user
from routes.decorators import resident_required
from models.request import CollectionRequest

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
