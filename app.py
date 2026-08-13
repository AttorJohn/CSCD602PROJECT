"""
WasteTrack Ghana - Entry point.

This is intentionally the smallest possible Flask app for now (Step 4
of the build plan). Database, models, auth and the resident/admin
workflows get added incrementally on top of this in later steps -
see README.md for the running checklist.
"""
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-change-me"  # TODO: move to env var before deployment

    @app.route("/")
    def home():
        return "Hello, WasteTrack Ghana! The Flask app is running."

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
