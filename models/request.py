"""CollectionRequest model - maps to the REQUEST entity in the ER diagram (Section 3.5).

Status follows the state machine in Section 3.4:
pending -> assigned -> in_progress -> collected
pending -> cancelled
"""
from datetime import datetime
from models import db

VALID_STATUSES = ("pending", "assigned", "in_progress", "collected", "cancelled")
VALID_WASTE_TYPES = ("household", "commercial", "recyclable", "other")


class CollectionRequest(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    collector_id = db.Column(db.Integer, db.ForeignKey("collectors.id"), nullable=True)

    address = db.Column(db.String(255), nullable=False)
    waste_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    preferred_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resident = db.relationship("User", back_populates="requests")
    collector = db.relationship("Collector", back_populates="requests")

    def __repr__(self):
        return f"<Request #{self.id} {self.status}>"
