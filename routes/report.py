from flask import Blueprint, render_template, request, session
from ai.report_generator import generate_session_report
from database.mongodb import get_user_mental_reports, get_user_relationship_reports, get_user_iq_reports
from routes.chat import TEMPORARY_CHAT_LOGS
from routes.iq import IQ_TEST_SESSIONS

report_bp = Blueprint('report', __name__)

@report_bp.route('/report', methods=['GET'])
def report():
    mode = request.args.get('type', request.args.get('mode', 'mental'))
    session_id = request.args.get('session_id', None)
    user_email = session.get('user_email', 'guest@mindsense.ai')
    user_name  = session.get('user_name', 'Guest User')

    # ── IQ Report: pull directly from active IQ session or MongoDB ──────────
    if mode == 'iq':
        iq_data = None

        # Try the active in-memory IQ session first (just-completed test)
        if session_id and session_id in IQ_TEST_SESSIONS:
            s = IQ_TEST_SESSIONS[session_id]
            responses = s.get('responses', [])
            total = len(responses) or 1
            correct = s.get('correct_count', 0)
            accuracy = round((correct / total) * 100)
            estimated_iq = max(80, min(145, 90 + int(accuracy * 0.5) + (5 if correct > 14 else 0)))
            percentile = max(25, min(99, int(estimated_iq * 0.7)))
            total_time = sum(r.get('time_taken', 15) for r in responses)

            if estimated_iq >= 120:
                cognitive_tier = "Superior Cognitive Performance"
                tier_badge = "bg-amber-500 text-white"
                summary = "You demonstrated exceptional pattern recognition, logical deduction, and abstract problem-solving under adaptive difficulty. This score places you well above the general population in analytical intelligence."
            elif estimated_iq >= 100:
                cognitive_tier = "Above Average Logical Ability"
                tier_badge = "bg-teal-500 text-white"
                summary = "You showed strong analytical processing and consistent performance across Easy and Medium logic challenges. Your reasoning skills are solid and above the population average."
            else:
                cognitive_tier = "Average Cognitive Profile"
                tier_badge = "bg-indigo-500 text-white"
                summary = "You completed foundational logic challenges with steady accuracy. Consistent practice with pattern recognition and numerical sequences will help improve your score over time."

            strengths = []
            categories_correct = {}
            for r in responses:
                cat = r.get('category', 'General')
                if r.get('is_correct'):
                    categories_correct[cat] = categories_correct.get(cat, 0) + 1

            if categories_correct:
                top_cats = sorted(categories_correct.items(), key=lambda x: x[1], reverse=True)[:2]
                strengths = [f"Strong performance in {c[0]}" for c in top_cats]
            if not strengths:
                strengths = ["Pattern Recognition", "Logical Deduction"]

            from datetime import datetime
            iq_data = {
                'report_type': 'iq',
                'title': 'Adaptive IQ & Cognitive Performance Assessment',
                'patient_name': user_name,
                'patient_email': user_email,
                'date': datetime.now().strftime("%B %d, %Y — %I:%M %p"),
                'primary_mood': 'Focused',
                'estimated_iq_score': estimated_iq,
                'cognitive_tier': cognitive_tier,
                'risk_badge': tier_badge,
                'accuracy': accuracy,
                'correct_answers': correct,
                'total_questions': total,
                'percentile': f"{percentile}th Percentile",
                'total_time_seconds': total_time,
                'summary': summary,
                'scores': {'stress': 10, 'anxiety': 10, 'depression': 5, 'overall': 15},
                'recommendations': strengths + [
                    "Practice spatial logic and matrix reasoning puzzles weekly.",
                    "Engage in analytical reading to broaden vocabulary and deduction ability.",
                    "Retake this assessment after 4–6 weeks of deliberate cognitive training."
                ]
            }

        # Fall back to MongoDB IQ reports
        if not iq_data:
            iq_reports = get_user_iq_reports(user_email)
            if iq_reports:
                iq_data = iq_reports[0]
                # Ensure all required fields are present
                if 'cognitive_tier' not in iq_data:
                    iq_data['cognitive_tier'] = 'Above Average Logical Ability'
                if 'risk_badge' not in iq_data:
                    iq_data['risk_badge'] = 'bg-teal-500 text-white'
                if 'summary' not in iq_data:
                    iq_data['summary'] = 'Cognitive assessment completed successfully.'
                if 'recommendations' not in iq_data:
                    iq_data['recommendations'] = ['Practice pattern recognition exercises regularly.']
                if 'primary_mood' not in iq_data:
                    iq_data['primary_mood'] = 'Focused'
                if 'accuracy' not in iq_data:
                    iq_data['accuracy'] = 0
                if 'correct_answers' not in iq_data:
                    iq_data['correct_answers'] = 0
                if 'total_questions' not in iq_data:
                    iq_data['total_questions'] = 20

        # Final fallback placeholder IQ report
        if not iq_data:
            from datetime import datetime
            iq_data = {
                'report_type': 'iq',
                'title': 'Adaptive IQ & Cognitive Performance Assessment',
                'patient_name': user_name,
                'patient_email': user_email,
                'date': datetime.now().strftime("%B %d, %Y — %I:%M %p"),
                'primary_mood': 'Focused',
                'estimated_iq_score': 118,
                'cognitive_tier': 'Above Average Logical Ability',
                'risk_badge': 'bg-teal-500 text-white',
                'accuracy': 75,
                'correct_answers': 15,
                'total_questions': 20,
                'percentile': '82nd Percentile',
                'summary': 'No completed IQ test sessions found. Please complete the Adaptive IQ Assessment to generate a personalized cognitive report.',
                'scores': {'stress': 10, 'anxiety': 10, 'depression': 5, 'overall': 15},
                'recommendations': [
                    'Complete the 20-question Adaptive IQ Test for a personalized assessment.',
                    'Practice numerical reasoning and pattern recognition exercises.',
                    'Engage in logical puzzles to improve abstract thinking.'
                ]
            }

        return render_template('report.html', report=iq_data)

    # ── Mental Health or Divorce Report ─────────────────────────────────────
    user_key = f"{user_email}_{mode}"
    logs = TEMPORARY_CHAT_LOGS.get(user_key, [])

    # Try any available logs if mode-specific is empty
    if not logs:
        for k, l in TEMPORARY_CHAT_LOGS.items():
            if k.startswith(user_email) and l:
                logs = l
                break

    if logs:
        emotions = [log.get('emotion', 'Neutral') for log in logs]
        most_common_emotion = max(set(emotions), key=emotions.count)
        scores_list = [log.get('scores', {}) for log in logs if log.get('scores')]
        avg_stress      = round(sum(s.get('stress', 25)      for s in scores_list) / max(len(scores_list), 1))
        avg_anxiety     = round(sum(s.get('anxiety', 20)     for s in scores_list) / max(len(scores_list), 1))
        avg_depression  = round(sum(s.get('depression', 15)  for s in scores_list) / max(len(scores_list), 1))
        avg_overall     = round(sum(s.get('overall', 30)     for s in scores_list) / max(len(scores_list), 1))
        emotion_stats   = {'emotion': most_common_emotion}
        mental_scores   = {'stress': avg_stress, 'anxiety': avg_anxiety, 'depression': avg_depression, 'overall': avg_overall}
    else:
        emotion_stats = {'emotion': 'Stress' if mode == 'divorce' else 'Calm'}
        mental_scores = {'stress': 40, 'anxiety': 30, 'depression': 20, 'overall': 45}

    report_data = generate_session_report(
        user_name, user_email, logs, emotion_stats, mental_scores, report_type=mode
    )

    return render_template('report.html', report=report_data)
