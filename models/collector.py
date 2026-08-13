"""Collector model - maps to the COLLECTOR entity in the ER diagram (Section 3.5)."""
from models import db


class Collector(db.Model):
    __tablename__ = "collectors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="available")  # available | busy

    # One collector -> many requests (Section 3.5, COLLECTOR 1 --- * REQUEST)
    requests = db.relationship(
        "CollectionRequest", back_populates="collector", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Collector {self.name}>"
