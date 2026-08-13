"""Authorisation decorators.

Implements FR-03 (role-based authorisation) and NFR-03: an admin
route must not be reachable by a resident account via a SERVER-SIDE
check, not merely a hidden UI link. @admin_required and
@resident_required both enforce login AND role in one decorator, so
a route only needs one of these - not @login_required as well.
"""
from functools import wraps
from flask import abort
from flask_login import login_required, current_user


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)  # logged in, but wrong role
        return view_func(*args, **kwargs)
    return wrapped


def resident_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "resident":
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped
