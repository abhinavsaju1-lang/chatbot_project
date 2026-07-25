from flask import Blueprint, render_template, session
from database.mongodb import get_user_chat_history, get_user_mental_reports, get_user_relationship_reports, get_user_iq_reports
from routes.chat import TEMPORARY_CHAT_LOGS
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    user_email = session.get('user_email', 'guest@mindsense.ai')
    user_name = session.get('user_name', 'Guest User')

    # Collect all in-memory session logs (mental + divorce)
    logs = TEMPORARY_CHAT_LOGS.get(f"{user_email}_mental", [])
    divorce_logs = TEMPORARY_CHAT_LOGS.get(f"{user_email}_divorce", [])
    all_temp = logs + divorce_logs

    # Also pull from MongoDB for persistence
    db_history = get_user_chat_history(user_email)
    total_sessions = max(len(all_temp), len(db_history))

    # --- Core Stats Calculation ---
    if all_temp:
        latest_emotion = all_temp[-1].get('emotion', 'Calm')
        scores_list = [log.get('scores', {}) for log in all_temp if log.get('scores')]
        avg_stress   = round(sum(s.get('stress', 25) for s in scores_list) / max(len(scores_list), 1))
        avg_anxiety  = round(sum(s.get('anxiety', 20) for s in scores_list) / max(len(scores_list), 1))
        avg_overall  = round(sum(s.get('overall', 30) for s in scores_list) / max(len(scores_list), 1))
    else:
        latest_emotion = 'Calm'
        avg_stress = 25
        avg_anxiety = 20
        avg_overall = 30

    # --- IQ Score ---
    iq_reports = get_user_iq_reports(user_email)
    latest_iq_score = iq_reports[0].get('estimated_iq_score', 118) if iq_reports else 118

    # --- Relationship Health ---
    rel_reports = get_user_relationship_reports(user_email)
    rel_health = rel_reports[0].get('conflict_intensity', 'Constructive Transition') if rel_reports else 'Constructive Transition'

    # --- Emotion Frequency Counts ---
    emotion_counts = {
        'Happy': 0, 'Sad': 0, 'Stress': 0,
        'Anxiety': 0, 'Depression': 0, 'Anger': 0,
        'Fear': 0, 'Loneliness': 0, 'Confusion': 0, 'Burnout': 0, 'Neutral': 1
    }
    for log in all_temp:
        em = log.get('emotion', 'Neutral')
        emotion_counts[em] = emotion_counts.get(em, 0) + 1

    # --- 7-Day Wellness & Stress Trend ---
    # Build a dict keyed by date string (Mon–Sun) with running averages
    today = datetime.now().date()
    day_labels = []
    day_wellness = []
    day_stress = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_label = day.strftime('%a')  # e.g., "Mon"
        day_labels.append(day_label)

        day_logs = [
            log for log in all_temp
            if _parse_log_date(log.get('timestamp', '')) == day
        ]

        if day_logs:
            w_avg = round(sum(log.get('scores', {}).get('overall', 30) for log in day_logs) / len(day_logs))
            s_avg = round(sum(log.get('scores', {}).get('stress', 25) for log in day_logs) / len(day_logs))
        else:
            # Use running average as placeholder so the chart isn't empty
            w_avg = max(20, avg_overall - (i * 2))
            s_avg = min(80, avg_stress + (i * 2))

        day_wellness.append(w_avg)
        day_stress.append(s_avg)

    stats = {
        'total_sessions': total_sessions,
        'latest_emotion': latest_emotion,
        'stress_index': avg_stress,
        'anxiety_score': avg_anxiety,
        'overall_wellness': avg_overall,
        'latest_iq_score': latest_iq_score,
        'relationship_health': rel_health,
        'emotion_counts': emotion_counts,
        'trend_labels': day_labels,
        'trend_wellness': day_wellness,
        'trend_stress': day_stress,
    }

    return render_template('dashboard.html', user_name=user_name, stats=stats)


def _parse_log_date(timestamp_str):
    """Try to parse a timestamp string to a date object. Returns None on failure."""
    if not timestamp_str:
        return None
    for fmt in ('%I:%M %p', '%B %d, %Y %I:%M %p', '%Y-%m-%d'):
        try:
            return datetime.strptime(timestamp_str, fmt).date()
        except (ValueError, TypeError):
            pass
    return None
