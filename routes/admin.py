from flask import Blueprint, render_template, session, redirect, url_for, flash

admin_bp = Blueprint("admin", __name__)

# ── Static dummy data — no MongoDB queries ────────────────────────────────────
DUMMY_USERS = [
    {"name": "Jane Doe",       "email": "jane.doe@example.com",    "is_admin": False, "created_at": "2026-07-01"},
    {"name": "John Smith",     "email": "john.smith@example.com",  "is_admin": False, "created_at": "2026-07-03"},
    {"name": "Admin User",     "email": "admin@mindsense.ai",      "is_admin": True,  "created_at": "2026-06-15"},
    {"name": "Alice Johnson",  "email": "alice.j@example.com",     "is_admin": False, "created_at": "2026-07-10"},
    {"name": "Bob Williams",   "email": "bob.w@example.com",       "is_admin": False, "created_at": "2026-07-12"},
]

DUMMY_REPORTS = [
    {
        "title": "Mental Health Session Report",
        "patient_name": "Jane Doe",
        "date": "2026-07-20",
        "risk_level": "Moderate",
        "risk_badge": "bg-amber-500/10 text-amber-600 border border-amber-500/20",
        "report_type": "mental",
        "session_id": "demo-session-001",
    },
    {
        "title": "Divorce Counseling Report",
        "patient_name": "John Smith",
        "date": "2026-07-18",
        "risk_level": "Low",
        "risk_badge": "bg-teal-500/10 text-teal-600 border border-teal-500/20",
        "report_type": "divorce",
        "session_id": "demo-session-002",
    },
    {
        "title": "Adaptive IQ Assessment Report",
        "patient_name": "Alice Johnson",
        "date": "2026-07-22",
        "risk_level": "Above Average",
        "risk_badge": "bg-indigo-500/10 text-indigo-600 border border-indigo-500/20",
        "report_type": "iq",
        "session_id": "demo-session-003",
    },
]

DUMMY_HIGH_RISK = [
    {
        "patient_name":  "Bob Williams",
        "patient_email": "bob.w@example.com",
        "stress_score":  82,
        "risk_level":    "Critical",
        "date":          "2026-07-23",
    },
    {
        "patient_name":  "Jane Doe",
        "patient_email": "jane.doe@example.com",
        "stress_score":  74,
        "risk_level":    "High",
        "date":          "2026-07-20",
    },
]


@admin_bp.route("/admin", methods=["GET"])
def admin():
    if not session.get("user_email"):
        flash("Please login to access the Admin Panel.", "warning")
        return redirect(url_for("auth.login"))

    try:
        from database.mongodb import get_all_users, get_all_reports, get_high_risk_users
        real_users = get_all_users()
        real_reports = get_all_reports()
        real_high_risk = get_high_risk_users()

        users = real_users if real_users else DUMMY_USERS
        reports = real_reports if real_reports else DUMMY_REPORTS
        high_risk_users = real_high_risk if real_high_risk else DUMMY_HIGH_RISK
    except Exception as e:
        print(f"[Admin] DB query exception: {e}")
        users = DUMMY_USERS
        reports = DUMMY_REPORTS
        high_risk_users = DUMMY_HIGH_RISK

    return render_template(
        "admin.html",
        users=users,
        reports=reports,
        high_risk_users=high_risk_users,
        search_query="",
    )
