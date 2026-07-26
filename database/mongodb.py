import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Module-level globals
# Using raw MongoClient instead of flask_pymongo for full Atlas SRV compatibility.
_client = None
_db     = None


class _MongoProxy:
    """Thin proxy so all existing mongo.db.collection calls work unchanged."""
    @property
    def db(self):
        return _db


mongo = _MongoProxy()


# ── Connection init (called once from app.py) ──────────────────────────────────
def init_db(app):
    """Connect to MongoDB Atlas using raw MongoClient. Pings on startup."""
    global _client, _db
    uri = app.config.get('MONGO_URI', '')
    if not uri:
        print("[DB] MONGO_URI is not set in config.")
        return None

    try:
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=10000,
            tls=True,                       # Atlas always requires TLS
            tlsAllowInvalidCertificates=False,
        )
        # Verify the connection is live before the first request hits
        _client.admin.command('ping')
        # Parse DB name from URI (e.g. .../mindsense_db?appName=...)
        db_name = uri.split('/')[-1].split('?')[0] or 'mindsense_db'
        _db = _client[db_name]
        print(f"[DB] Connected to MongoDB Atlas — database: '{db_name}'")
        return _client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[DB] MongoDB connection FAILED: {e}")
        return None
    except Exception as e:
        print(f"[DB] Unexpected MongoDB error during init: {e}")
        return None


# ── 1. USERS ───────────────────────────────────────────────────────────────────
def get_user_by_email(email):
    """Retrieve a user document by email address."""
    try:
        if mongo.db is not None:
            return mongo.db.users.find_one({"email": email})
    except Exception as e:
        print(f"[DB] get_user_by_email error: {e}")
    return None


def create_user(user_data):
    """Insert a new user document into the users collection."""
    try:
        if mongo.db is not None:
            return mongo.db.users.insert_one(user_data)
    except Exception as e:
        print(f"[DB] create_user error: {e}")
    return None


def get_all_users():
    """Return all users (password excluded) for the Admin Panel."""
    try:
        if mongo.db is not None:
            return list(mongo.db.users.find({}, {"_id": 0, "password": 0}))
    except Exception as e:
        print(f"[DB] get_all_users error: {e}")
    return []


# ── 2. HIGH-RISK MONITORING ────────────────────────────────────────────────────
def get_high_risk_users():
    """Return users with stress score >= 65 for Admin intervention monitoring."""
    high_risk_list = []
    try:
        if mongo.db is not None:
            reports = list(mongo.db.mental_reports.find(
                {"scores.stress": {"$gte": 65}}, {"_id": 0}
            ))
            for rep in reports:
                high_risk_list.append({
                    'patient_name':  rep.get('patient_name', 'Anonymous'),
                    'patient_email': rep.get('patient_email', 'N/A'),
                    'stress_score':  rep.get('scores', {}).get('stress', 75),
                    'risk_level':    rep.get('risk_level', 'High Risk'),
                    'date':          rep.get('date', 'Recent'),
                })
    except Exception as e:
        print(f"[DB] get_high_risk_users error: {e}")
    return high_risk_list


# ── 3. CHAT SESSIONS ───────────────────────────────────────────────────────────
def save_chat_session(session_data):
    try:
        if mongo.db is not None:
            return mongo.db.chat_sessions.insert_one(session_data)
    except Exception as e:
        print(f"[DB] save_chat_session error: {e}")
    return None


def get_user_chat_history(user_id, mode=None):
    try:
        if mongo.db is not None:
            query = {"user_id": user_id}
            if mode:
                query["mode"] = mode
            return list(mongo.db.chat_sessions.find(query).sort("timestamp", 1))
    except Exception as e:
        print(f"[DB] get_user_chat_history error: {e}")
    return []


def clear_user_chat_history(user_id, mode):
    try:
        if mongo.db is not None:
            mongo.db.chat_sessions.delete_many({"user_id": user_id, "mode": mode})
            return True
    except Exception as e:
        print(f"[DB] clear_user_chat_history error: {e}")
    return False


# ── 4. MENTAL REPORTS ─────────────────────────────────────────────────────────
def save_mental_report(report_data):
    try:
        if mongo.db is not None:
            return mongo.db.mental_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB] save_mental_report error: {e}")
    return None


def get_user_mental_reports(user_id):
    try:
        if mongo.db is not None:
            return list(mongo.db.mental_reports.find(
                {"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB] get_user_mental_reports error: {e}")
    return []


# ── 5. RELATIONSHIP REPORTS ───────────────────────────────────────────────────
def save_relationship_report(report_data):
    try:
        if mongo.db is not None:
            return mongo.db.relationship_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB] save_relationship_report error: {e}")
    return None


def get_user_relationship_reports(user_id):
    try:
        if mongo.db is not None:
            return list(mongo.db.relationship_reports.find(
                {"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB] get_user_relationship_reports error: {e}")
    return []


# ── 6. IQ REPORTS ─────────────────────────────────────────────────────────────
def save_iq_report(report_data):
    try:
        if mongo.db is not None:
            return mongo.db.iq_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB] save_iq_report error: {e}")
    return None


def get_user_iq_reports(user_id):
    try:
        if mongo.db is not None:
            return list(mongo.db.iq_reports.find(
                {"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB] get_user_iq_reports error: {e}")
    return []


# ── 7. ALL REPORTS (Admin) ────────────────────────────────────────────────────
def get_all_reports():
    reports = []
    try:
        if mongo.db is not None:
            reports.extend(list(mongo.db.mental_reports.find(
                {}, {"_id": 0}).sort("timestamp", -1)))
            reports.extend(list(mongo.db.relationship_reports.find(
                {}, {"_id": 0}).sort("timestamp", -1)))
            reports.extend(list(mongo.db.iq_reports.find(
                {}, {"_id": 0}).sort("timestamp", -1)))
    except Exception as e:
        print(f"[DB] get_all_reports error: {e}")
    return reports


def delete_report(report_id, report_type='mental'):
    try:
        if mongo.db is not None:
            coll_name = (f"{report_type}_reports"
                         if not report_type.endswith('_reports')
                         else report_type)
            mongo.db[coll_name].delete_one({"session_id": report_id})
            return True
    except Exception as e:
        print(f"[DB] delete_report error: {e}")
    return False


# ── 8. FEEDBACK ───────────────────────────────────────────────────────────────
def save_feedback(feedback_data):
    try:
        if mongo.db is not None:
            return mongo.db.feedback.insert_one(feedback_data)
    except Exception as e:
        print(f"[DB] save_feedback error: {e}")
    return None
