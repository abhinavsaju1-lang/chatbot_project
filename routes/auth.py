"""
auth.py — MindSense AI Authentication Routes
Completely self-contained. Zero AI/LLM imports. Direct PyMongo calls only.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import traceback
import sys
from database.mongodb import mongo   # direct PyMongo instance — no helper wrappers

auth_bp = Blueprint("auth", __name__)


def _users():
    """Return the raw PyMongo 'users' collection. Raises if DB is unavailable."""
    return mongo.db.users


# ══════════════════════════════════════════════════════════════════════════════
#  /login  — handles both Register and Sign In (tab-based single page)
# ══════════════════════════════════════════════════════════════════════════════
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action", "login")

        # ─── REGISTER ─────────────────────────────────────────────────────────
        if action == "register":
            # EXACT field names from login.html  ─ do NOT change these keys
            name     = request.form.get("name", "").strip()
            gender   = request.form.get("gender", "Prefer not to say").strip()
            email    = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()

            # ── Validation ────────────────────────────────────────────────────
            if not name or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("login.html", active_tab="register")

            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("login.html", active_tab="register")

            # ── Database: check duplicate, then insert ────────────────────────
            try:
                users_col = _users()
                if users_col is None:
                    raise Exception("Database collection (_users) is None. The database connection might not be established.")

                existing = users_col.find_one({"email": email})
                if existing:
                    flash("Email already registered. Please sign in.", "warning")
                    return render_template("login.html", active_tab="login")

                result = users_col.insert_one({
                    "name":       name,
                    "gender":     gender,
                    "email":      email,
                    # pbkdf2:sha256 — explicit algorithm so check_password_hash always matches
                    "password":   generate_password_hash(password, method="pbkdf2:sha256"),
                    "is_admin":   email.endswith("@mindsense.ai"),
                    "created_at": "2026-08-01",
                })
                print(f"[Auth] Successfully inserted user: {email}. Inserted ID: {result.inserted_id}", flush=True)
            except Exception as db_err:
                print(f"\\n--- REGISTRATION ERROR ---", file=sys.stderr, flush=True)
                print(f"[Auth] Registration DB error: {db_err}", file=sys.stderr, flush=True)
                traceback.print_exc()
                print(f"--------------------------\\n", file=sys.stderr, flush=True)
                flash("Registration failed due to a database error. Please try again.", "danger")
                return render_template("login.html", active_tab="register")

            # ── Auto-login after successful registration ───────────────────────
            session["user_email"]  = email
            session["user_name"]   = name
            session["user_gender"] = gender
            session["is_admin"]    = email.endswith("@mindsense.ai")
            flash(f"Welcome, {name}! Your account has been created.", "success")
            return redirect(url_for("dashboard.dashboard"))

        # ─── SIGN IN ──────────────────────────────────────────────────────────
        else:
            # EXACT field names from login.html  ─ do NOT change these keys
            email    = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()

            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html", active_tab="login")

            # ── Database: fetch user and verify hash ───────────────────────────
            try:
                users_col = _users()
                if users_col is None:
                    raise Exception("Database collection (_users) is None. The database connection might not be established.")
                user = users_col.find_one({"email": email})
            except Exception as db_err:
                print(f"\\n--- LOGIN ERROR ---", file=sys.stderr, flush=True)
                print(f"[Auth] Login DB error: {db_err}", file=sys.stderr, flush=True)
                traceback.print_exc()
                print(f"-------------------\\n", file=sys.stderr, flush=True)
                flash("Login failed due to a database error. Please try again.", "danger")
                return render_template("login.html", active_tab="login")

            if not user or not check_password_hash(user["password"], password):
                flash("Invalid email or password.", "danger")
                return render_template("login.html", active_tab="login")

            session["user_email"]  = user["email"]
            session["user_name"]   = user["name"]
            session["user_gender"] = user.get("gender", "Prefer not to say")
            session["is_admin"]    = user.get("is_admin", False)
            return redirect(url_for("dashboard.dashboard"))

    active_tab = request.args.get("tab", "login")
    return render_template("login.html", active_tab=active_tab)


# ══════════════════════════════════════════════════════════════════════════════
#  /logout
# ══════════════════════════════════════════════════════════════════════════════
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login") + "?tab=login")
