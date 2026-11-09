from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from bson import ObjectId
from ai.chatbot import get_chatbot_response, is_crisis_intent, get_crisis_response
from database.mongodb import (
    get_db,
    get_user_by_email,
    save_chat_session,
    get_user_chat_history,
    clear_user_chat_history,
    save_mental_report,
    save_relationship_report
)
from ai.report_generator import generate_session_report

chat_bp = Blueprint('chat', __name__)

# Temporary in-memory chat logs and past bot responses per user and module
TEMPORARY_CHAT_LOGS = {}
PAST_BOT_RESPONSES_WINDOW = {}

def get_current_user_profile():
    """
    Fetches the profile for the currently logged in user directly from MongoDB.
    Checks session['user_id'] or session['user_email'], queries MongoDB,
    and returns a normalized dict with name, gender, email, and user_id.
    """
    user_email = session.get('user_email')
    user_id = session.get('user_id')
    user_doc = None

    try:
        db = get_db()
        if db is not None:
            if user_id:
                try:
                    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
                except Exception:
                    pass
            if not user_doc and user_email:
                user_doc = db.users.find_one({"email": user_email.lower().strip()})
    except Exception as e:
        print(f"[Counseling DB Profile Warning] {e}")

    # Resolve values with session fallbacks
    name = (user_doc.get('name') if user_doc else None) or session.get('user_name') or 'Guest User'
    email = (user_doc.get('email') if user_doc else None) or user_email or 'guest@mindsense.ai'
    gender = (user_doc.get('gender') if user_doc else None) or session.get('user_gender') or 'Prefer not to say'

    # Keep session keys synchronized
    session['user_name'] = name
    session['user_email'] = email
    session['user_gender'] = gender
    if user_doc and '_id' in user_doc:
        session['user_id'] = str(user_doc['_id'])

    return {
        'name': name,
        'email': email,
        'gender': gender,
        'user_id': session.get('user_id', email)
    }

@chat_bp.route('/chat', methods=['GET'])
def chat_page():
    mode = request.args.get('mode', 'mental')
    profile = get_current_user_profile()
    user_email = profile['email']
    user_name = profile['name']

    user_key = f"{user_email}_{mode}"

    # Load persistent history for this specific module from MongoDB if empty in-memory
    if user_key not in TEMPORARY_CHAT_LOGS or not TEMPORARY_CHAT_LOGS[user_key]:
        db_history = get_user_chat_history(user_email, mode=mode)
        TEMPORARY_CHAT_LOGS[user_key] = []
        if db_history:
            for item in db_history:
                TEMPORARY_CHAT_LOGS[user_key].append({
                    'user': item.get('message'),
                    'bot': item.get('bot_response'),
                    'mode': item.get('mode', mode),
                    'emotion': item.get('emotion', 'Calm'),
                    'timestamp': item.get('timestamp').strftime("%I:%M %p") if isinstance(item.get('timestamp'), datetime) else str(item.get('timestamp'))
                })

    history_for_mode = TEMPORARY_CHAT_LOGS.get(user_key, [])
    return render_template('chat.html', mode=mode, user_name=user_name, history=history_for_mode)

@chat_bp.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        mode = data.get('mode', 'mental')

        if not user_message:
            return jsonify({'success': False, 'error': 'Message cannot be empty.'}), 400

        profile = get_current_user_profile()
        user_email = profile['email']
        user_name = profile['name']
        user_gender = profile['gender']

        user_key = f"{user_email}_{mode}"
        if user_key not in TEMPORARY_CHAT_LOGS:
            TEMPORARY_CHAT_LOGS[user_key] = []
        if user_key not in PAST_BOT_RESPONSES_WINDOW:
            PAST_BOT_RESPONSES_WINDOW[user_key] = []

        history_list = TEMPORARY_CHAT_LOGS[user_key]
        past_bot_responses = PAST_BOT_RESPONSES_WINDOW[user_key]

        # Generate intent-driven, empathetic response with dynamic profile injection
        ai_result = get_chatbot_response(
            user_message,
            mode=mode,
            history_list=history_list,
            past_bot_responses=past_bot_responses,
            user_gender=user_gender,
            user_name=user_name,
            user_email=user_email
        )

        bot_response = ai_result['bot_response']
        detected_intent = ai_result['intent']
        detected_emotion = ai_result['emotion']
        sentiment_data = ai_result['sentiment']
        context_used = ai_result['context_used']

        # Keep last 5 bot responses in anti-repetition memory window
        past_bot_responses.append(bot_response)
        if len(past_bot_responses) > 5:
            past_bot_responses.pop(0)

        chat_entry = {
            'user': user_message,
            'bot': bot_response,
            'mode': mode,
            'intent': detected_intent,
            'emotion': detected_emotion,
            'timestamp': datetime.now().strftime("%I:%M %p"),
            'scores': sentiment_data['scores']
        }
        TEMPORARY_CHAT_LOGS[user_key].append(chat_entry)

        # Save turn to MongoDB chat_sessions
        session_record = {
            'user_id': user_email,
            'user_name': user_name,
            'mode': mode,
            'message': user_message,
            'bot_response': bot_response,
            'intent': detected_intent,
            'emotion': detected_emotion,
            'sentiment_scores': sentiment_data['sentiment'],
            'mental_scores': sentiment_data['scores'],
            'timestamp': datetime.now()
        }
        try:
            save_chat_session(session_record)
        except Exception as db_err:
            print(f"[DB Warning] Could not save chat session: {db_err}")

        # Update reports
        try:
            report_data = generate_session_report(
                user_name, user_email, TEMPORARY_CHAT_LOGS[user_key],
                {'emotion': detected_emotion},
                sentiment_data['scores'],
                report_type=mode
            )

            if mode == 'divorce':
                save_relationship_report(report_data)
            else:
                save_mental_report(report_data)
        except Exception as rep_err:
            print(f"[Report Warning] Could not save counseling report: {rep_err}")

        return jsonify({
            'success': True,
            'mode': mode,
            'message': user_message,
            'response': bot_response,
            'intent': detected_intent,
            'emotion': detected_emotion,
            'sentiment': sentiment_data['sentiment'],
            'scores': sentiment_data['scores'],
            'rag_context': context_used[:200] + "..." if context_used else None
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Counseling Route Error] {e}")
        if 'user_message' in locals() and is_crisis_intent(user_message):
            fallback_reply = get_crisis_response(user_name=user_name if 'user_name' in locals() else 'there')
            crisis_intent = 'Crisis'
            crisis_emotion = 'High Risk'
            crisis_scores = {'stress': 95, 'anxiety': 95, 'depression': 95, 'overall': 95}
        else:
            fallback_reply = (
                "I'm here with you, and what you're sharing matters. We hit a momentary processing delay, "
                "but I want to understand. Could you please share that with me once more?"
            )
            crisis_intent = 'General'
            crisis_emotion = 'Supportive'
            crisis_scores = {'stress': 50, 'anxiety': 30, 'depression': 30, 'overall': 40}

        return jsonify({
            'success': True,
            'mode': mode if 'mode' in locals() else 'mental',
            'message': user_message if 'user_message' in locals() else '',
            'response': fallback_reply,
            'intent': crisis_intent,
            'emotion': crisis_emotion,
            'sentiment': {'compound': -0.9 if crisis_intent == 'Crisis' else 0.0, 'pos': 0.0, 'neu': 0.1, 'neg': 0.9 if crisis_intent == 'Crisis' else 0.0},
            'scores': crisis_scores,
            'rag_context': 'Crisis Intervention Protocol' if crisis_intent == 'Crisis' else None
        })

@chat_bp.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear persistent chat history for a specific module when user clicks 'New Chat'."""
    data = request.get_json() or {}
    mode = data.get('mode', 'mental')
    user_email = session.get('user_email', 'guest@mindsense.ai')

    user_key = f"{user_email}_{mode}"
    TEMPORARY_CHAT_LOGS[user_key] = []
    PAST_BOT_RESPONSES_WINDOW[user_key] = []

    clear_user_chat_history(user_email, mode)
    return jsonify({'success': True, 'message': f'New chat session started for {mode} mode.'})

@chat_bp.route('/history', methods=['GET'])
def history():
    user_email = session.get('user_email', 'guest@mindsense.ai')
    db_history = get_user_chat_history(user_email)

    display_history = []
    if db_history:
        for item in db_history:
            display_history.append({
                'user': item.get('message'),
                'bot': item.get('bot_response'),
                'mode': item.get('mode', 'mental'),
                'emotion': item.get('emotion', 'Calm'),
                'timestamp': item.get('timestamp').strftime("%B %d, %Y %I:%M %p") if isinstance(item.get('timestamp'), datetime) else str(item.get('timestamp'))
            })
    else:
        for k, logs in TEMPORARY_CHAT_LOGS.items():
            if k.startswith(user_email):
                display_history.extend(logs)

    return render_template('history.html', history=display_history, user_name=session.get('user_name', 'Guest'))
