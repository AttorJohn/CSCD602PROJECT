from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance - imported by every model file
# and by app.py. Defined here (not inside a model file) to avoid
# circular imports.
db = SQLAlchemy()

# Import models AFTER db is defined so db.create_all() can see them.
from models.user import User  # noqa: E402,F401
from models.collector import Collector  # noqa: E402,F401
from models.request import CollectionRequest  # noqa: E402,F401
