"""Admin-facing routes - dashboard, collector management, and request
lifecycle management.

Implements FR-07 (view all requests), FR-08 (assign collector) and
FR-09 (update status), enforcing the legal transitions from the
request state diagram (Project Documentation, Section 3.4).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from routes.decorators import admin_required
from models import db
from models.request import CollectionRequest, VALID_STATUSES
from models.collector import Collector
from models.audit import AuditLog, record_audit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Legal status transitions - mirrors Section 3.4 exactly:
# pending -> assigned -> in_progress -> collected, or pending -> cancelled.
ALLOWED_TRANSITIONS = {
    "pending": {"assigned", "cancelled"},
    "assigned": {"in_progress"},
    "in_progress": {"collected"},
    "collected": set(),
    "cancelled": set(),
}


@admin_bp.route("/")
@admin_required
def dashboard():
    selected_status = request.args.get("status", "").strip().lower()
    if selected_status not in VALID_STATUSES:
        selected_status = ""

    all_requests = CollectionRequest.query.order_by(CollectionRequest.created_at.desc()).all()
    requests = (
        [collection_request for collection_request in all_requests if collection_request.status == selected_status]
        if selected_status
        else all_requests
    )
    status_counts = {
        status: sum(collection_request.status == status for collection_request in all_requests)
        for status in VALID_STATUSES
    }
    collectors = Collector.query.order_by(Collector.name).all()
    available_collectors = [collector for collector in collectors if collector.status == "available"]
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template(
        "admin_dashboard.html",
        requests=requests,
        collectors=collectors,
        available_collectors=available_collectors,
        status_counts=status_counts,
        statuses=VALID_STATUSES,
        selected_status=selected_status,
        audit_logs=audit_logs,
    )


@admin_bp.route("/collectors/new", methods=["POST"])
@admin_required
def add_collector():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name:
        flash("Collector name is required.", "error")
        return redirect(url_for("admin.dashboard"))

    collector = Collector(name=name, phone=phone or None, status="available")
    db.session.add(collector)
    record_audit(current_user, "Added collector", details=collector.name)
    db.session.commit()
    flash(f"Collector '{name}' added.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/requests/<int:request_id>/assign", methods=["POST"])
@admin_required
def assign_collector(request_id):
    req = db.get_or_404(CollectionRequest, request_id)
    collector_id = request.form.get("collector_id", type=int)

    if req.status != "pending":
        flash(f"Request #{req.id:04d} is no longer pending and cannot be assigned.", "error")
        return redirect(url_for("admin.dashboard"))

    collector = db.session.get(Collector, collector_id) if collector_id else None
    if not collector:
        flash("Please choose a valid collector.", "error")
        return redirect(url_for("admin.dashboard"))
    if collector.status != "available":
        flash(f"{collector.name} is currently busy and cannot be assigned.", "error")
        return redirect(url_for("admin.dashboard"))

    req.collector_id = collector.id
    req.status = "assigned"
    collector.status = "busy"
    record_audit(current_user, "Assigned collector", req.id, collector.name)
    db.session.commit()
    flash(f"Request #{req.id:04d} assigned to {collector.name}.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/requests/<int:request_id>/status", methods=["POST"])
@admin_required
def update_status(request_id):
    req = db.get_or_404(CollectionRequest, request_id)
    new_status = request.form.get("new_status", "")

    allowed = ALLOWED_TRANSITIONS.get(req.status, set())
    if new_status not in allowed:
        flash(
            f"Cannot move request #{req.id:04d} from '{req.status}' to '{new_status}'.",
            "error",
        )
        return redirect(url_for("admin.dashboard"))

    previous_status = req.status
    req.status = new_status
    if new_status == "collected" and req.collector:
        req.collector.status = "available"
    record_audit(current_user, "Updated request status", req.id, f"{previous_status} -> {new_status}")
    db.session.commit()
    flash(
        f"Request #{req.id:04d} status updated to {new_status.replace('_', ' ').title()}.",
        "success",
    )
    return redirect(url_for("admin.dashboard"))
