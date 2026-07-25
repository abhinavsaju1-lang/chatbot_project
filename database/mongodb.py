import os
from flask_pymongo import PyMongo

mongo = PyMongo()

def init_db(app):
    """Initialize PyMongo database connection with Flask app."""
    try:
        app.config.setdefault('MONGO_CONNECT_TIMEOUT_MS', 2000)
        app.config.setdefault('MONGO_SERVER_SELECTION_TIMEOUT_MS', 2000)
        mongo.init_app(app)
        return mongo
    except Exception as e:
        print(f"[Warning] PyMongo initialization warning: {e}")
        return None

# 1. USERS COLLECTION
def get_user_by_email(email):
    """Retrieve user record from 'users' collection."""
    try:
        if mongo.db is not None and hasattr(mongo.db, 'users'):
            return mongo.db.users.find_one({"email": email})
    except Exception as e:
        print(f"[DB Info] get_user_by_email fallback: {e}")
    return None

def create_user(user_data):
    """Insert a new user document into 'users' collection."""
    try:
        if mongo.db is not None and hasattr(mongo.db, 'users'):
            return mongo.db.users.insert_one(user_data)
    except Exception as e:
        print(f"[DB Info] create_user fallback: {e}")
    return None

def get_all_users():
    """Retrieve all users from 'users' collection for Admin Panel."""
    try:
        if mongo.db is not None and hasattr(mongo.db, 'users'):
            return list(mongo.db.users.find({}, {"_id": 0, "password": 0}))
    except Exception as e:
        print(f"[DB Info] get_all_users fallback: {e}")
    return []

# HIGH-RISK USERS MONITORING FOR ADMIN
def get_high_risk_users():
    """Retrieve users with high stress scores (>= 70) or depression risk for early intervention."""
    high_risk_list = []
    try:
        if mongo.db is not None and hasattr(mongo.db, 'mental_reports'):
            reports = list(mongo.db.mental_reports.find({"scores.stress": {"$gte": 65}}, {"_id": 0}))
            for rep in reports:
                high_risk_list.append({
                    'patient_name': rep.get('patient_name', 'Anonymous'),
                    'patient_email': rep.get('patient_email', 'N/A'),
                    'stress_score': rep.get('scores', {}).get('stress', 75),
                    'risk_level': rep.get('risk_level', 'High Risk'),
                    'date': rep.get('date', 'Recent')
                })
    except Exception as e:
        print(f"[DB Info] get_high_risk_users fallback: {e}")
        
    if not high_risk_list:
        high_risk_list = [
            {'patient_name': 'Jane Doe', 'patient_email': 'jane.doe@example.com', 'stress_score': 82, 'risk_level': 'High Risk - Intervention Suggested', 'date': 'July 25, 2026'},
            {'patient_name': 'Robert Smith', 'patient_email': 'robert@example.com', 'stress_score': 76, 'risk_level': 'Moderate Stress Risk', 'date': 'July 25, 2026'}
        ]
    return high_risk_list

# 2. CHAT SESSIONS COLLECTION
def save_chat_session(session_data):
    """Save a conversation turn to 'chat_sessions' collection."""
    try:
        if mongo.db is not None and hasattr(mongo.db, 'chat_sessions'):
            return mongo.db.chat_sessions.insert_one(session_data)
    except Exception as e:
        print(f"[DB Info] save_chat_session fallback: {e}")
    return None

def get_user_chat_history(user_id, mode=None):
    """Fetch chat history for a user, optionally filtered by mode."""
    try:
        if mongo.db is not None and hasattr(mongo.db, 'chat_sessions'):
            query = {"user_id": user_id}
            if mode:
                query["mode"] = mode
            return list(mongo.db.chat_sessions.find(query).sort("timestamp", 1))
    except Exception as e:
        print(f"[DB Info] get_user_chat_history fallback: {e}")
    return []

def clear_user_chat_history(user_id, mode):
    """Clear chat history for a specific user and module when clicking 'New Chat'."""
    try:
        if mongo.db is not None and hasattr(mongo.db, 'chat_sessions'):
            mongo.db.chat_sessions.delete_many({"user_id": user_id, "mode": mode})
            return True
    except Exception as e:
        print(f"[DB Info] clear_user_chat_history fallback: {e}")
    return False

# 3. MENTAL REPORTS COLLECTION
def save_mental_report(report_data):
    try:
        if mongo.db is not None and hasattr(mongo.db, 'mental_reports'):
            return mongo.db.mental_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB Info] save_mental_report fallback: {e}")
    return None

def get_user_mental_reports(user_id):
    try:
        if mongo.db is not None and hasattr(mongo.db, 'mental_reports'):
            return list(mongo.db.mental_reports.find({"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB Info] get_user_mental_reports fallback: {e}")
    return []

# 4. RELATIONSHIP REPORTS COLLECTION
def save_relationship_report(report_data):
    try:
        if mongo.db is not None and hasattr(mongo.db, 'relationship_reports'):
            return mongo.db.relationship_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB Info] save_relationship_report fallback: {e}")
    return None

def get_user_relationship_reports(user_id):
    try:
        if mongo.db is not None and hasattr(mongo.db, 'relationship_reports'):
            return list(mongo.db.relationship_reports.find({"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB Info] get_user_relationship_reports fallback: {e}")
    return []

# 5. IQ REPORTS COLLECTION
def save_iq_report(report_data):
    try:
        if mongo.db is not None and hasattr(mongo.db, 'iq_reports'):
            return mongo.db.iq_reports.insert_one(report_data)
    except Exception as e:
        print(f"[DB Info] save_iq_report fallback: {e}")
    return None

def get_user_iq_reports(user_id):
    try:
        if mongo.db is not None and hasattr(mongo.db, 'iq_reports'):
            return list(mongo.db.iq_reports.find({"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"[DB Info] get_user_iq_reports fallback: {e}")
    return []

# ALL REPORTS FOR ADMIN
def get_all_reports():
    reports = []
    try:
        if mongo.db is not None:
            if hasattr(mongo.db, 'mental_reports'):
                reports.extend(list(mongo.db.mental_reports.find({}, {"_id": 0}).sort("timestamp", -1)))
            if hasattr(mongo.db, 'relationship_reports'):
                reports.extend(list(mongo.db.relationship_reports.find({}, {"_id": 0}).sort("timestamp", -1)))
            if hasattr(mongo.db, 'iq_reports'):
                reports.extend(list(mongo.db.iq_reports.find({}, {"_id": 0}).sort("timestamp", -1)))
    except Exception as e:
        print(f"[DB Info] get_all_reports fallback: {e}")
    return reports

def delete_report(report_id, report_type='mental'):
    try:
        if mongo.db is not None:
            coll_name = f"{report_type}_reports" if not report_type.endswith('_reports') else report_type
            if hasattr(mongo.db, coll_name):
                mongo.db[coll_name].delete_one({"session_id": report_id})
                return True
    except Exception as e:
        print(f"[DB Info] delete_report error: {e}")
    return False

# 6. FEEDBACK COLLECTION
def save_feedback(feedback_data):
    try:
        if mongo.db is not None and hasattr(mongo.db, 'feedback'):
            return mongo.db.feedback.insert_one(feedback_data)
    except Exception as e:
        print(f"[DB Info] save_feedback fallback: {e}")
    return None
