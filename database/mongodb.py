import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure, ConfigurationError

# Fix for dnspython on Windows / Docker / Render containers where system nameservers list is empty
try:
    import dns.resolver
    resolver = dns.resolver.get_default_resolver()
    if not resolver.nameservers:
        resolver.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
    resolver.timeout = 2.0
    resolver.lifetime = 4.0
except Exception:
    pass

# Module-level globals
_client = None
_db     = None
_last_error = None

def get_db_error():
    """Returns the last encountered MongoDB initialization or connection error."""
    global _last_error
    return _last_error

def get_db():
    """
    Lazily retrieves the database instance, reconnecting if needed.
    Checks Flask application context first, then module globals.
    """
    global _client, _db

    # 1. Return cached active database instance if already available
    if _db is not None:
        return _db

    # 2. Check Flask application context if running inside request
    try:
        from flask import current_app, has_app_context
        if has_app_context():
            if hasattr(current_app, "mongo_db") and current_app.mongo_db is not None:
                _db = current_app.mongo_db
                return _db
            # Try initializing with current_app
            init_db(current_app)
            if _db is not None:
                return _db
    except Exception:
        pass

    # 3. Fallback: Initialize directly
    init_db()
    return _db

class _MongoProxy:
    """Thin proxy so all existing mongo.db.collection calls work unchanged."""
    @property
    def db(self):
        return get_db()

mongo = _MongoProxy()

def init_db(app=None):
    """
    Connect to MongoDB Atlas using raw MongoClient with TLS & certifi.
    Binds the client and database to both module globals and app context.
    """
    global _client, _db, _last_error

    uri = ""
    if app is not None and hasattr(app, "config"):
        uri = app.config.get('MONGO_URI', '') or app.config.get('MONGODB_URI', '')
    if not uri:
        uri = os.getenv("MONGO_URI", "") or os.getenv("MONGODB_URI", "")
    if not uri:
        try:
            from flask import current_app, has_app_context
            if has_app_context() and hasattr(current_app, "config"):
                uri = current_app.config.get('MONGO_URI', '') or current_app.config.get('MONGODB_URI', '')
        except Exception:
            pass
    if not uri:
        try:
            from config import Config
            uri = Config.MONGO_URI
        except Exception:
            pass

    # Sanitize URI string (strip accidental whitespace or wrapping quotes from Render dashboard)
    if uri:
        uri = uri.strip().strip("'\"").strip()

    if not uri:
        _last_error = "MONGO_URI is not set in environment or config."
        print(f"[DB Warning] {_last_error}")
        return None

    try:
        client_kwargs = {
            "serverSelectionTimeoutMS": 7000,
            "connectTimeoutMS": 7000,
            "socketTimeoutMS": 10000,
            "retryWrites": True,
        }

        # Check for Atlas / TLS
        is_srv = uri.startswith("mongodb+srv://")
        if is_srv or "ssl=true" in uri.lower() or "tls=true" in uri.lower():
            client_kwargs["tls"] = True
            try:
                client_kwargs["tlsCAFile"] = certifi.where()
            except Exception:
                pass

        try:
            _client = MongoClient(uri, **client_kwargs)
        except Exception as client_init_err:
            # If failed with tlsCAFile, retry without it as fallback
            if "tlsCAFile" in client_kwargs:
                client_kwargs.pop("tlsCAFile", None)
                _client = MongoClient(uri, **client_kwargs)
            else:
                raise client_init_err

        # Parse or determine the database name cleanly
        try:
            _db = _client.get_default_database()
        except Exception:
            _db = None

        if _db is None:
            try:
                clean_uri = uri.split('?')[0].rstrip('/')
                db_name = clean_uri.split('/')[-1] if '/' in clean_uri else 'mindsense_db'
                if not db_name or db_name.startswith("mongodb"):
                    db_name = 'mindsense_db'
                _db = _client[db_name]
            except Exception:
                _db = _client['mindsense_db']

        # Bind to Flask app object if provided
        if app is not None:
            app.mongo_client = _client
            app.mongo_db = _db
            if not hasattr(app, "extensions"):
                app.extensions = {}
            app.extensions["mongodb"] = _db

        # Test cluster connectivity
        try:
            _client.admin.command('ping')
            _last_error = None
            print(f"[DB] Successfully connected and pinged MongoDB — database: '{_db.name}'")
        except ServerSelectionTimeoutError as sste:
            _last_error = f"ServerSelectionTimeoutError: {sste}"
            print(f"[DB Warning] Could not reach MongoDB cluster: {sste}")
            print("[DB Diagnostic] TIP: If hosted on Render, ensure MongoDB Atlas Network Access has IP 0.0.0.0/0 (Allow Access from Anywhere) enabled!")
        except OperationFailure as of:
            _last_error = f"OperationFailure: {of}"
            print(f"[DB Warning] MongoDB Authentication failed: {of}")
            print("[DB Diagnostic] TIP: Check your MongoDB Atlas username and password in MONGO_URI.")
        except Exception as ping_err:
            _last_error = f"Ping failed: {ping_err}"
            print(f"[DB Warning] MongoDB ping check failed: {ping_err}")

        return _client

    except Exception as e:
        _last_error = str(e)
        print(f"[DB Error] Failed to initialize MongoClient: {e}")
        return None

def check_db_health():
    """Diagnostic check returning connection status and actionable tips."""
    global _client, _db, _last_error
    db = get_db()
    if db is None or _client is None:
        return {
            "connected": False,
            "error": _last_error or "MongoClient could not be initialized.",
            "hint": "Check if MONGO_URI is set properly in Render Environment variables."
        }
    try:
        _client.admin.command('ping')
        return {
            "connected": True,
            "database": db.name,
            "collections": db.list_collection_names()
        }
    except ServerSelectionTimeoutError as e:
        return {
            "connected": False,
            "error": f"Timeout connecting to cluster: {e}",
            "hint": "Render IP was rejected by MongoDB Atlas. Go to MongoDB Atlas -> Network Access -> Add IP Address -> Select 'Allow Access from Anywhere' (0.0.0.0/0)."
        }
    except OperationFailure as e:
        return {
            "connected": False,
            "error": f"Authentication failed: {e}",
            "hint": "Check username and password in MONGO_URI. If password contains special characters like @, %, #, URL-encode them."
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "hint": "Verify your MongoDB Atlas cluster is active (not paused) and MONGO_URI format is correct."
        }


# ── 1. USERS ───────────────────────────────────────────────────────────────────
def get_user_by_email(email):
    """Retrieve a user document by email address."""
    try:
        db = get_db()
        if db is not None:
            return db.users.find_one({"email": email})
    except Exception as e:
        print(f"[DB] get_user_by_email error: {e}")
    return None


def create_user(user_data):
    """Insert a new user document into the users collection."""
    try:
        db = get_db()
        if db is not None:
            return db.users.insert_one(user_data)
    except Exception as e:
        print(f"[DB] create_user error: {e}")
    return None


def get_all_users():
    """Return all users (password excluded) for the Admin Panel."""
    try:
        db = get_db()
        if db is not None:
            return list(db.users.find({}, {"_id": 0, "password": 0}))
    except Exception as e:
        print(f"[DB] get_all_users error: {e}")
    return []


# ── 2. HIGH-RISK MONITORING ────────────────────────────────────────────────────
def get_high_risk_users():
    """Return users with stress score >= 65 for Admin intervention monitoring."""
    high_risk_list = []
    try:
        db = get_db()
        if db is not None:
            reports = list(db.mental_reports.find(
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
        db = get_db()
        if db is not None:
            return db.chat_sessions.insert_one(session_data)
    except Exception as e:
        print(f"[DB] save_chat_session error: {e}")
    return None


def get_user_chat_history(user_id, mode=None):
    try:
        db = get_db()
        if db is not None:
            query = {"user_id": user_id}
            if mode:
                query["mode"] = mode
            return list(db.chat_sessions.find(query).sort("timestamp", 1))
    except Exception as e:
        print(f"[DB] get_user_chat_history error: {e}")
    return []


def clear_user_chat_history(user_id, mode):
    try:
        db = get_db()
        if db is not None:
            db.chat_sessions.delete_many({"user_id": user_id, "mode": mode})
            return True
    except Exception as e:
        print(f"[DB] clear_user_chat_history error: {e}")
    return False


# ── 4. MENTAL REPORTS ─────────────────────────────────────────────────────────
def save_mental_report(report_data):
    try:
        db = get_db()
        if db is not None:
            return db.mental_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB] save_mental_report error: {e}")
    return None


def get_user_mental_reports(user_id):
    try:
        db = get_db()
        if db is not None:
            return list(db.mental_reports.find(
                {"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB] get_user_mental_reports error: {e}")
    return []


# ── 5. RELATIONSHIP REPORTS ───────────────────────────────────────────────────
def save_relationship_report(report_data):
    try:
        db = get_db()
        if db is not None:
            return db.relationship_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB] save_relationship_report error: {e}")
    return None


def get_user_relationship_reports(user_id):
    try:
        db = get_db()
        if db is not None:
            return list(db.relationship_reports.find(
                {"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB] get_user_relationship_reports error: {e}")
    return []


# ── 6. IQ REPORTS ─────────────────────────────────────────────────────────────
def save_iq_report(report_data):
    try:
        db = get_db()
        if db is not None:
            return db.iq_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB] save_iq_report error: {e}")
    return None


def get_user_iq_reports(user_id):
    try:
        db = get_db()
        if db is not None:
            return list(db.iq_reports.find(
                {"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB] get_user_iq_reports error: {e}")
    return []


# ── 7. ALL REPORTS (Admin) ────────────────────────────────────────────────────
def get_all_reports():
    reports = []
    try:
        db = get_db()
        if db is not None:
            reports.extend(list(db.mental_reports.find(
                {}, {"_id": 0}).sort("timestamp", -1)))
            reports.extend(list(db.relationship_reports.find(
                {}, {"_id": 0}).sort("timestamp", -1)))
            reports.extend(list(db.iq_reports.find(
                {}, {"_id": 0}).sort("timestamp", -1)))
    except Exception as e:
        print(f"[DB] get_all_reports error: {e}")
    return reports


def delete_report(report_id, report_type='mental'):
    try:
        db = get_db()
        if db is not None:
            coll_name = (f"{report_type}_reports"
                         if not report_type.endswith('_reports')
                         else report_type)
            db[coll_name].delete_one({"session_id": report_id})
            return True
    except Exception as e:
        print(f"[DB] delete_report error: {e}")
    return False


# ── 8. FEEDBACK ───────────────────────────────────────────────────────────────
def save_feedback(feedback_data):
    try:
        db = get_db()
        if db is not None:
            return db.feedback.insert_one(feedback_data)
    except Exception as e:
        print(f"[DB] save_feedback error: {e}")
    return None
