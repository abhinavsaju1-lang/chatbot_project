"""
auth.py — MindSense AI Authentication Routes
Direct PyMongo calls with robust Atlas connection diagnostics.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import traceback
import sys
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure, ConfigurationError
from database.mongodb import mongo, check_db_health, get_db, get_db_error

auth_bp = Blueprint("auth", __name__)


def _users():
    """Return the raw PyMongo 'users' collection or None if DB is unavailable."""
    db = get_db()
    if db is None:
        return None
    return db.users


@auth_bp.route("/api/db-health", methods=["GET"])
def db_health_check():
    """Diagnostic endpoint to verify MongoDB Atlas connection on Render."""
    health = check_db_health()
    status_code = 200 if health.get("connected") else 503
    return jsonify(health), status_code


# ══════════════════════════════════════════════════════════════════════════════
#  /login  — handles both Register and Sign In (tab-based single page)
# ══════════════════════════════════════════════════════════════════════════════
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action", "login")

        # ─── REGISTER ─────────────────────────────────────────────────────────
        if action == "register":
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
                    db_detail = get_db_error() or "Database instance is not initialized. Please verify your MONGO_URI in Render."
                    raise ConnectionError(f"Database unavailable: {db_detail}")

                existing = users_col.find_one({"email": email})
                if existing:
                    flash("Email already registered. Please sign in.", "warning")
                    return render_template("login.html", active_tab="login")

                result = users_col.insert_one({
                    "name":       name,
                    "gender":     gender,
                    "email":      email,
                    "password":   generate_password_hash(password, method="pbkdf2:sha256"),
                    "is_admin":   email.endswith("@mindsense.ai"),
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                })
                print(f"[Auth] Successfully inserted user: {email}. Inserted ID: {result.inserted_id}", flush=True)

            except ServerSelectionTimeoutError as sste:
                print(f"\n--- REGISTRATION DB TIMEOUT ERROR ---\n{sste}\n", file=sys.stderr, flush=True)
                flash(
                    "Database connection timed out! If deployed on Render, please go to MongoDB Atlas -> Network Access -> Add IP Address -> '0.0.0.0/0' (Allow access from anywhere).",
                    "danger"
                )
                return render_template("login.html", active_tab="register")

            except OperationFailure as of:
                print(f"\n--- REGISTRATION DB AUTH ERROR ---\n{of}\n", file=sys.stderr, flush=True)
                flash(
                    "Database authentication failed. Please verify your MongoDB Atlas username and password in the MONGO_URI environment variable.",
                    "danger"
                )
                return render_template("login.html", active_tab="register")

            except Exception as db_err:
                print(f"\n--- REGISTRATION DB ERROR ---", file=sys.stderr, flush=True)
                print(f"[Auth] Registration error: {db_err}", file=sys.stderr, flush=True)
                traceback.print_exc()
                print(f"-----------------------------\n", file=sys.stderr, flush=True)

                err_str = str(db_err).lower()
                if "timeout" in err_str or "connection" in err_str:
                    flash(
                        "Database connection failed. Ensure MongoDB Atlas Network Access allows connections from anywhere (0.0.0.0/0).",
                        "danger"
                    )
                else:
                    flash(f"Registration failed: {db_err}", "danger")
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
            email    = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()

            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html", active_tab="login")

            # ── Database: fetch user and verify hash ───────────────────────────
            try:
                users_col = _users()
                if users_col is None:
                    db_detail = get_db_error() or "Database instance is not initialized. Please verify your MONGO_URI in Render."
                    raise ConnectionError(f"Database unavailable: {db_detail}")
                user = users_col.find_one({"email": email})

            except ServerSelectionTimeoutError as sste:
                print(f"\n--- LOGIN DB TIMEOUT ERROR ---\n{sste}\n", file=sys.stderr, flush=True)
                flash(
                    "Database connection timed out! If deployed on Render, please enable '0.0.0.0/0' (Allow access from anywhere) in MongoDB Atlas Network Access.",
                    "danger"
                )
                return render_template("login.html", active_tab="login")

            except OperationFailure as of:
                print(f"\n--- LOGIN DB AUTH ERROR ---\n{of}\n", file=sys.stderr, flush=True)
                flash(
                    "Database authentication failed. Please check your MongoDB username and password in MONGO_URI.",
                    "danger"
                )
                return render_template("login.html", active_tab="login")

            except Exception as db_err:
                print(f"\n--- LOGIN ERROR ---", file=sys.stderr, flush=True)
                print(f"[Auth] Login DB error: {db_err}", file=sys.stderr, flush=True)
                traceback.print_exc()
                print(f"-------------------\n", file=sys.stderr, flush=True)
                flash(f"Login failed due to database error: {db_err}", "danger")
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
