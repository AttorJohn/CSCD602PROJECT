# WasteTrack Ghana

Web-based waste collection request & tracking system.
CSCD602 Advanced Software Engineering — Individual Project Examination.

## Current status
The homepage (`/`) now renders a real landing page with Login/Register
buttons for anonymous visitors, or a "Go to Dashboard" button (pointed
at the right dashboard) if you're already logged in — it was still
returning the plain "Hello, WasteTrack!" text from Step 4 before this.

Steps 11-15 of the build plan complete in one pass:
- **Admin dashboard** (`/admin/`) — lists every request from every
  resident (FR-07), with a small collector-management form since
  collectors have to exist before they can be assigned to anything.
- **Collector assignment & status changes** (FR-08, FR-09) — admin
  can assign a collector to a pending request, then move it forward
  through the lifecycle (Assigned → Start Collection → Mark
  Collected), or cancel a pending one. Every transition is checked
  server-side against the state diagram (Section 3.4) — you cannot,
  for example, jump straight from Pending to Collected.
- **Error handling** — custom 403/404/500 pages instead of raw
  Flask defaults.
- **UI refinement** — responsive tables (horizontal scroll on small
  screens), mobile-friendly header, consistent button styling across
  resident and admin views.
- **Tests** — a pytest suite (`tests/`) covering registration, login,
  request validation, dashboard isolation between residents, admin
  role-blocking, collector assignment, and illegal status transitions.

See `Project_Documentation` for the full requirements, estimation,
design and technical debt plan behind this project.

## Run it locally
1. Create and activate a virtual environment:
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python app.py`
4. Log in as `admin@wastetrack.gh` (create one first if you haven't —
   see Step 8 above) — you should land on `/admin/`
5. Add a collector using the small form at the top of the page
6. As a resident, submit a request if you don't already have a
   pending one
7. Back as admin, refresh the dashboard — the request should appear
   with an "Assign" dropdown; pick your collector and click Assign
8. Status badge should flip to "Assigned"; click "Start Collection",
   then "Mark Collected" — watch it move through the lifecycle
9. Try visiting a nonsense URL like `/this-does-not-exist` — you
   should see the styled 404 page, not a raw Flask error screen
10. Run the automated test suite: `pytest` — all tests should pass

## Run the tests
```
pytest
```
Tests run against an in-memory SQLite database (see `tests/conftest.py`),
so they never touch your real `instance/wastetrack.db`.

## Build plan (from Project Documentation, Section 2.6)
- [x] Step 1: Project setup & Git
- [x] Step 2: Virtual environment
- [x] Step 3: Install Flask
- [x] Step 4: Minimal "Hello, WasteTrack!" app
- [x] Step 5: Add the database (SQLAlchemy + SQLite) - User, CollectionRequest, Collector models created together since they share one ER diagram
- [x] Step 6: Registration (`/register`, hashed passwords)
- [x] Step 7: Login/logout (Flask-Login sessions)
- [x] Step 8: Role-based authorisation (`@admin_required`, `@resident_required`, `flask create-admin`)
- [x] Step 9: Resident dashboard (`/dashboard`, lists own requests)
- [x] Step 10: Submit collection request (`/dashboard/new`, validated before saving)
- [x] Step 11: Admin dashboard (`/admin/`, view all requests + manage collectors)
- [x] Step 12: Collector assignment / status changes (enforced against the state diagram)
- [x] Step 13: Custom error pages (403 / 404 / 500)
- [x] Step 14: UI refinement (responsive tables, mobile nav)
- [x] Step 15: Automated tests (`pytest`, in-memory DB, 15 tests across auth/requests/admin)
- [ ] Step 16: Push to GitHub
- [ ] Step 17: Deploy to Render
- [ ] Step 18: Test live app
- [ ] Step 19: Documentation

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
