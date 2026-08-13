"""Collector self-service registration and assigned-work dashboard."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from routes.decorators import collector_required
from models import db
from models.audit import record_audit
from models.collector import Collector
from models.request import CollectionRequest

collector_bp = Blueprint("collector", __name__, url_prefix="/collector")


@collector_bp.route("/")
@collector_required
def dashboard():
    collector = Collector.query.filter_by(user_id=current_user.id).first_or_404()
    assigned_requests = collector.requests.order_by(CollectionRequest.created_at.desc()).all()
    return render_template("collector_dashboard.html", collector=collector, requests=assigned_requests)


@collector_bp.route("/requests/<int:request_id>/status", methods=["POST"])
@collector_required
def update_status(request_id):
    collector = Collector.query.filter_by(user_id=current_user.id).first_or_404()
    collection_request = CollectionRequest.query.filter_by(
        id=request_id, collector_id=collector.id
    ).first_or_404()
    next_status = request.form.get("new_status", "")
    allowed = {"assigned": "in_progress", "in_progress": "collected"}

    if allowed.get(collection_request.status) != next_status:
        flash("That request status update is not allowed.", "error")
        return redirect(url_for("collector.dashboard"))

    previous_status = collection_request.status
    collection_request.status = next_status
    if next_status == "collected":
        collector.status = "available"
    record_audit(
        current_user, "Collector updated request status", collection_request.id,
        f"{previous_status} -> {next_status}",
    )
    db.session.commit()
    flash(f"Request #{collection_request.id:04d} updated to {next_status.replace('_', ' ').title()}.", "success")
    return redirect(url_for("collector.dashboard"))
