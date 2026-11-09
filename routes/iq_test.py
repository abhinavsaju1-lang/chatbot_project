from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import uuid
from ai.iq_generator import generate_iq_test_batch
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
    print("--- /API/IQ/START ROUTE HIT! ---", flush=True)
    user_email = session.get('user_email', 'candidate@mindsense.ai')
    session_id = str(uuid.uuid4())

    try:
        # Batch generate all 20 questions dynamically
        questions_batch = generate_iq_test_batch()
        if not questions_batch or len(questions_batch) == 0:
            from ai.iq_questions import get_fallback_iq_batch
            questions_batch = get_fallback_iq_batch()

        IQ_TEST_SESSIONS[session_id] = {
            'session_id': session_id,
            'user_email': user_email,
            'questions': questions_batch, # store all questions
            'question_index': 1,
            'total_questions': len(questions_batch),
            'correct_count': 0,
            'responses': [],
            'start_time': datetime.now()
        }

        # Fetch first question from memory
        question = questions_batch[0]
        IQ_TEST_SESSIONS[session_id]['current_question'] = question

        return jsonify({
            'success': True,
            'session_id': session_id,
            'question_index': 1,
            'total_questions': len(questions_batch),
            'difficulty': question['difficulty'].capitalize(),
            'category': question['category'],
            'question': question['question'],
            'options': question['options'],
            'time_limit': 30
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            from ai.iq_questions import get_fallback_iq_batch
            fallback_batch = get_fallback_iq_batch()
            IQ_TEST_SESSIONS[session_id] = {
                'session_id': session_id,
                'user_email': user_email,
                'questions': fallback_batch,
                'question_index': 1,
                'total_questions': len(fallback_batch),
                'correct_count': 0,
                'responses': [],
                'start_time': datetime.now()
            }
            question = fallback_batch[0]
            IQ_TEST_SESSIONS[session_id]['current_question'] = question
            return jsonify({
                'success': True,
                'session_id': session_id,
                'question_index': 1,
                'total_questions': len(fallback_batch),
                'difficulty': question['difficulty'].capitalize(),
                'category': question['category'],
                'question': question['question'],
                'options': question['options'],
                'time_limit': 30
            })
        except Exception:
            err_msg = "The AI assessment engine is currently busy or experiencing high traffic. Please try again in a few moments."
            return jsonify({'success': False, 'error': err_msg, 'details': str(e)}), 500

@iq_bp.route('/api/iq/next', methods=['POST'])
def next_iq_question():
    """Evaluate submitted answer, return correct answer for 1s visual feedback, and queue next question."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        user_answer = data.get('answer')
        time_taken = data.get('time_taken', 15)

        if not session_id or session_id not in IQ_TEST_SESSIONS:
            return jsonify({'success': False, 'error': 'Invalid or expired test session. Please restart.'}), 400

        test_state = IQ_TEST_SESSIONS[session_id]
        current_q = test_state['current_question']

        # Evaluate correctness
        is_correct = (user_answer == current_q['answer'])
        if is_correct:
            test_state['correct_count'] += 1

        test_state['responses'].append({
            'question_id': current_q['id'],
            'category': current_q['category'],
            'difficulty': current_q['difficulty'],
            'question': current_q['question'],
            'user_answer': user_answer,
            'correct_answer': current_q['answer'],
            'is_correct': is_correct,
            'time_taken': time_taken,
            'explanation': current_q.get('explanation', '')
        })

        test_state['question_index'] += 1

        # Check if completed
        if test_state['question_index'] > test_state['total_questions']:
            return finish_iq_test(session_id, current_q['answer'], is_correct)

        # Fetch next question from memory
        next_idx = test_state['question_index'] - 1
        next_q = test_state['questions'][next_idx]
        test_state['current_question'] = next_q

        return jsonify({
            'success': True,
            'session_id': session_id,
            'is_correct': is_correct,
            'correct_answer': current_q['answer'],
            'next_question_data': {
                'question_index': test_state['question_index'],
                'total_questions': test_state['total_questions'],
                'difficulty': next_q['difficulty'].capitalize(),
                'category': next_q['category'],
                'question': next_q['question'],
                'options': next_q['options'],
                'time_limit': 30
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to process question response. Please try again.'}), 500

def finish_iq_test(session_id, last_correct_answer, is_correct):
    """Complete test, calculate IQ score, percentile, and save report to MongoDB iq_reports."""
    test_state = IQ_TEST_SESSIONS.get(session_id, {})
    user_name = session.get('user_name', 'Test Candidate')
    user_email = session.get('user_email', 'candidate@mindsense.ai')

    responses = test_state.get('responses', [])
    total = len(responses) or 1
    correct = test_state.get('correct_count', 0)
    accuracy = round((correct / total) * 100)

    # Calculate weighted IQ score
    base_iq = 85
    weighted_score = 0
    for r in responses:
        if r['is_correct']:
            if r['difficulty'] == 'hard':
                weighted_score += 3
            elif r['difficulty'] == 'medium':
                weighted_score += 2
            else:
                weighted_score += 1
                
    estimated_iq = max(80, min(145, base_iq + weighted_score))
    
    # Calculate percentile based on normal distribution mean 100, sd 15
    import math
    def calculate_percentile(iq):
        z = (iq - 100) / 15.0
        return int(0.5 * (1 + math.erf(z / math.sqrt(2))) * 100)
        
    percentile = calculate_percentile(estimated_iq)
    
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
        'weaknesses': ['Spatial Math'],
        'responses': responses # Include responses and explanations
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
