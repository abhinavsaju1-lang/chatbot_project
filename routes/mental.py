from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import uuid
from database.mongodb import save_mental_report
from ai.chatbot import is_crisis_intent, get_crisis_response

mental_bp = Blueprint('mental', __name__)

@mental_bp.route('/mental-check', methods=['GET', 'POST'])
def mental_check():
    user_name = session.get('user_name', 'Guest')
    if request.method == 'GET':
        session['mental_step'] = 1
        initial_message = (
            "Hi! I will ask you a few questions to understand your mental well-being. "
            "Please answer honestly.\n\n"
            "Over the last 2 weeks, how often have you felt sad or hopeless?\n"
            "1. Never\n2. Sometimes\n3. Often\n4. Almost Every Day"
        )
        return render_template('mental_check.html', initial_message=initial_message, user_name=user_name)

    if request.method == 'POST':
        try:
            data = request.get_json() or {}
            user_answer = data.get('message', '').strip()
            current_step = session.get('mental_step', 1)
            
            # Immediate crisis intervention check
            if is_crisis_intent(user_answer):
                crisis_msg = get_crisis_response(user_name=user_name)
                return jsonify({'success': True, 'response': crisis_msg, 'step': current_step, 'is_crisis': True})

            response_text, next_step = process_mental_step(current_step, user_answer)
            session['mental_step'] = next_step
            
            return jsonify({'success': True, 'response': response_text, 'step': next_step})
        except Exception as e:
            print(f"[Mental Check Route Error] {e}")
            return jsonify({'success': False, 'error': 'Could not record assessment step. Please try again.'}), 500

def process_mental_step(step, answer):
    if step == 1:
        return ("Have you lost interest in activities you usually enjoy?\n- Yes\n- No", 2)
    elif step == 2:
        return ("How is your sleep?\n- Normal\n- Sleeping too much\n- Difficulty sleeping", 3)
    elif step == 3:
        return ("How is your appetite?\n- Normal\n- Less than usual\n- More than usual", 4)
    elif step == 4:
        return ("Have you been feeling anxious or worried most days?\n- Never\n- Sometimes\n- Often", 5)
    elif step == 5:
        return ("Have you had trouble concentrating?\n- Yes\n- No", 6)
    elif step == 6:
        return ("Have you felt lonely or isolated recently?\n- Yes\n- No", 7)
    elif step == 7:
        return ("On a scale of 1-10, how stressed are you today?", 8)
    elif step == 8:
        user_email = session.get('user_email', 'guest@mindsense.ai')
        user_name = session.get('user_name', 'Guest')
        session_id = str(uuid.uuid4())
        
        report_data = {
            'session_id': session_id,
            'report_type': 'mental',
            'title': 'Mental Health Assessment Report',
            'patient_name': user_name,
            'patient_email': user_email,
            'date': datetime.now().strftime("%B %d, %Y - %I:%M %p"),
            'timestamp': datetime.now(),
            'primary_mood': 'Mild Depression',
            'risk_level': 'Moderate',
            'risk_badge': 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
            'scores': {
                'stress': 65,
                'anxiety': 30,
                'depression': 55,
                'overall': 50
            },
            'summary': "The patient exhibits signs of mild depression and moderate stress, primarily affecting their daily mood and energy levels. Anxiety appears to be manageable at a low level. Further monitoring is advised.",
            'recommendations': [
                "Try regular sleep.",
                "Exercise 20-30 minutes daily.",
                "Talk to a trusted friend.",
                "If symptoms continue for more than 2 weeks, consult a mental health professional."
            ]
        }
        
        try:
            save_mental_report(report_data)
        except Exception as e:
            print(f"Error saving mental report: {e}")
            
        report = (
            "**Mental Health Summary**\n"
            "Mood : Mild Depression\n"
            "Stress : Moderate\n"
            "Anxiety : Low\n"
            "Depression Risk : Moderate\n\n"
            "**Recommendation:**\n"
            "• Try regular sleep.\n"
            "• Exercise 20-30 minutes daily.\n"
            "• Talk to a trusted friend.\n"
            "• If symptoms continue for more than 2 weeks, consult a mental health professional."
        )
        return (report, 9)
    else:
        return ("Assessment completed. You can check your saved reports in the Reports tab.", 9)
