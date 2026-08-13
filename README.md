# WasteTrack Ghana

Web-based waste collection request & tracking system.
CSCD602 Advanced Software Engineering — Individual Project Examination.

## Current status
Step 5 of the build plan complete: SQLite database wired up via
SQLAlchemy, with User, CollectionRequest and Collector models
matching the ER diagram (Project Documentation, Section 3.5). Visit
`/db-check` after starting the app to confirm the database connected
and the tables were created. See `Project_Documentation` for the
full requirements, estimation, design and technical debt plan
behind this project.

## Run it locally
1. Create and activate a virtual environment:
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python app.py`
4. Open http://127.0.0.1:5000 — should show the Hello World message
5. Open http://127.0.0.1:5000/db-check — should show
   "Database connected. Users table has 0 row(s)."
6. Check that `instance/wastetrack.db` now exists in your project folder

## Build plan (from Project Documentation, Section 2.6)
- [x] Step 1: Project setup & Git
- [x] Step 2: Virtual environment
- [x] Step 3: Install Flask
- [x] Step 4: Minimal "Hello, WasteTrack!" app
- [x] Step 5: Add the database (SQLAlchemy + SQLite) - User, CollectionRequest, Collector models created together since they share one ER diagram
- [ ] Step 6: Registration
- [ ] Step 7: Login/logout
- [ ] Step 9: Role-based authorisation
- [ ] Step 10: Resident dashboard
- [ ] Step 11: Collection requests
- [ ] Step 12: Admin dashboard
- [ ] Step 13: Collector assignment / status changes
- [ ] Step 14: Validation & error handling
- [ ] Step 15: UI refinement
- [ ] Step 16: Tests
- [ ] Step 17: Push to GitHub
- [ ] Step 18: Deploy to Render
- [ ] Step 19: Test live app
- [ ] Step 20: Documentation

## Project structure
```
wastetrack-ghana/
├── app.py
├── requirements.txt
├── models/       # SQLAlchemy models (User, Request, Collector)
├── routes/       # Flask blueprints (auth, resident, admin)
├── templates/    # Jinja2 HTML templates
├── static/       # CSS and JS
├── tests/        # pytest test suite
└── instance/     # SQLite database file (not committed)
```
