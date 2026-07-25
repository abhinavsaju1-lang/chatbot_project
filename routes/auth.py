from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.mongodb import get_user_by_email, create_user
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If already signed in, go straight to dashboard
    if "user_email" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        action = request.form.get("action", "login")

        # ─── REGISTER ────────────────────────────────────────────────────────
        if action == "register":
            name     = request.form.get("name", "").strip()
            email    = request.form.get("reg_email", "").strip().lower()
            password = request.form.get("reg_password", "").strip()

            if not name or not email or not password:
                flash("All fields are required for registration.", "danger")
                return render_template("login.html", active_tab="register")

            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("login.html", active_tab="register")

            existing = get_user_by_email(email)
            if existing:
                flash("Email already registered. Please sign in instead.", "warning")
                return render_template("login.html", active_tab="login")

            user_doc = {
                "name": name,
                "email": email,
                "password": generate_password_hash(password),
                "is_admin": email.endswith("@mindsense.ai"),
                "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
            }
            create_user(user_doc)

            # Auto-login immediately after registration
            session.permanent = True
            session["user_email"] = email
            session["user_name"]  = name
            session["is_admin"]   = user_doc["is_admin"]
            flash(f"Welcome, {name}! Your account has been created.", "success")
            return redirect(url_for("dashboard.dashboard"))

        # ─── SIGN IN ─────────────────────────────────────────────────────────
        else:
            email    = request.form.get("login_email", "").strip().lower()
            password = request.form.get("login_password", "").strip()
            remember = request.form.get("remember_me") == "on"

            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html", active_tab="login")

            user = get_user_by_email(email)
            if not user or not check_password_hash(user.get("password", ""), password):
                flash("Invalid credentials. Please try again.", "danger")
                return render_template("login.html", active_tab="login")

            session.permanent = remember
            session["user_email"] = user["email"]
            session["user_name"]  = user["name"]
            session["is_admin"]   = user.get("is_admin", False)
            return redirect(url_for("dashboard.dashboard"))

    active_tab = request.args.get("tab", "login")
    return render_template("login.html", active_tab=active_tab)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out. See you soon!", "info")
    return redirect(url_for("auth.login") + "?tab=login")
