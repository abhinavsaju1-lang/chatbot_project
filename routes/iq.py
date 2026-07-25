from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import uuid
from ai.iq_questions import get_adaptive_question, IQ_QUESTION_BANK
from database.mongodb import save_iq_report

iq_bp = Blueprint('iq', __name__)

IQ_TEST_SESSIONS = {}

@iq_bp.route('/iq', methods=['GET'])
def iq_test_page():
    user_name = session.get('user_name', 'Test Candidate')
    return render_template('iq_test.html', user_name=user_name)

@iq_bp.route('/api/iq/start', methods=['POST'])
def start_iq_test():
    """Start a new 20-question adaptive IQ test session."""
    user_email = session.get('user_email', 'candidate@mindsense.ai')
    session_id = str(uuid.uuid4())

    IQ_TEST_SESSIONS[session_id] = {
        'session_id': session_id,
        'user_email': user_email,
        'current_difficulty': 'easy',
        'question_index': 1,
        'total_questions': 20,
        'correct_count': 0,
        'asked_ids': [],
        'responses': [],
        'start_time': datetime.now()
    }

    # Fetch first question (Easy level)
    question = get_adaptive_question('easy', asked_ids=[])
    IQ_TEST_SESSIONS[session_id]['asked_ids'].append(question['id'])
    IQ_TEST_SESSIONS[session_id]['current_question'] = question

    return jsonify({
        'success': True,
        'session_id': session_id,
        'question_index': 1,
        'total_questions': 20,
        'difficulty': 'Easy',
        'category': question['category'],
        'question': question['question'],
        'options': question['options'],
        'time_limit': 30
    })

@iq_bp.route('/api/iq/next', methods=['POST'])
def next_iq_question():
    """Evaluate submitted answer, return correct answer for 1s visual feedback, and queue next question."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    user_answer = data.get('answer')
    time_taken = data.get('time_taken', 15)

    if not session_id or session_id not in IQ_TEST_SESSIONS:
        return jsonify({'success': False, 'error': 'Invalid test session.'}), 400

    test_state = IQ_TEST_SESSIONS[session_id]
    current_q = test_state['current_question']

    # Evaluate correctness
    is_correct = (user_answer == current_q['answer'])
    if is_correct:
        test_state['correct_count'] += 1

    test_state['responses'].append({
        'question_id': current_q['id'],
        'category': current_q['category'],
        'difficulty': test_state['current_difficulty'],
        'question': current_q['question'],
        'user_answer': user_answer,
        'correct_answer': current_q['answer'],
        'is_correct': is_correct,
        'time_taken': time_taken
    })

    # Adaptive difficulty scaling: Correct -> Hard, Incorrect -> Easy
    if is_correct:
        test_state['current_difficulty'] = 'hard'
    else:
        test_state['current_difficulty'] = 'easy'

    test_state['question_index'] += 1

    # Check if 20 questions completed
    if test_state['question_index'] > test_state['total_questions']:
        return finish_iq_test(session_id, current_q['answer'], is_correct)

    # Fetch next question adaptively
    next_q = get_adaptive_question(test_state['current_difficulty'], asked_ids=test_state['asked_ids'])
    test_state['asked_ids'].append(next_q['id'])
    test_state['current_question'] = next_q

    return jsonify({
        'success': True,
        'session_id': session_id,
        'is_correct': is_correct,
        'correct_answer': current_q['answer'],
        'next_question_data': {
            'question_index': test_state['question_index'],
            'total_questions': test_state['total_questions'],
            'difficulty': test_state['current_difficulty'].capitalize(),
            'category': next_q['category'],
            'question': next_q['question'],
            'options': next_q['options'],
            'time_limit': 30
        }
    })

def finish_iq_test(session_id, last_correct_answer, is_correct):
    """Complete test, calculate IQ score, percentile, and save report to MongoDB iq_reports."""
    test_state = IQ_TEST_SESSIONS.get(session_id, {})
    user_name = session.get('user_name', 'Test Candidate')
    user_email = session.get('user_email', 'candidate@mindsense.ai')

    responses = test_state.get('responses', [])
    total = len(responses) or 1
    correct = test_state.get('correct_count', 0)
    accuracy = round((correct / total) * 100)

    estimated_iq = max(80, min(145, 90 + int(accuracy * 0.5) + (5 if correct > 14 else 0)))
    percentile = max(25, min(99, int(estimated_iq * 0.7)))
    total_time = sum(r.get('time_taken', 15) for r in responses)

    report_data = {
        'session_id': session_id,
        'report_type': 'iq',
        'title': 'Adaptive IQ & Cognitive Performance Assessment',
        'patient_name': user_name,
        'patient_email': user_email,
        'date': datetime.now().strftime("%B %d, %Y - %I:%M %p"),
        'timestamp': datetime.now(),
        'estimated_iq_score': estimated_iq,
        'percentile': f"{percentile}th Percentile",
        'accuracy': accuracy,
        'total_time_seconds': total_time,
        'correct_answers': correct,
        'total_questions': total,
        'strengths': ['Pattern Recognition', 'Logical Deduction'],
        'weaknesses': ['Spatial Math']
    }

    save_iq_report(report_data)

    return jsonify({
        'success': True,
        'is_completed': True,
        'is_correct': is_correct,
        'correct_answer': last_correct_answer,
        'session_id': session_id,
        'iq_score': estimated_iq,
        'percentile': f"{percentile}th Percentile",
        'accuracy': accuracy,
        'redirect_url': f'/report?type=iq&session_id={session_id}'
    })
