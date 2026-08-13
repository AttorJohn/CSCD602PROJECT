"""User model - maps to the USER entity in the ER diagram (Section 3.5)."""
from datetime import datetime, timezone
from flask_login import UserMixin
from models import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="resident")  # "resident" | "admin"
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # One resident -> many requests (Section 3.5, USER 1 --- * REQUEST)
    requests = db.relationship(
        "CollectionRequest", back_populates="resident", lazy="dynamic"
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
