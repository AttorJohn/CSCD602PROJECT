"""Immutable-style activity records for important application events."""
from datetime import datetime, timezone
from models import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, nullable=True)
    actor_name = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    request_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


def record_audit(actor, action, request_id=None, details=None):
    """Add an audit entry to the current transaction."""
    db.session.add(AuditLog(
        actor_id=actor.id if actor else None,
        actor_name=actor.name if actor else "System",
        action=action,
        request_id=request_id,
        details=details,
    ))
