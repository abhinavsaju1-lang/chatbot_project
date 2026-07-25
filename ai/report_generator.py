from datetime import datetime

def generate_session_report(user_name, user_email, messages, emotion_stats, mental_scores, report_type='mental'):
    """
    Synthesize post-session report for Mental Health, Divorce Counseling, or IQ Cognitive Evaluation.
    """
    now = datetime.now()
    formatted_date = now.strftime("%B %d, %Y - %I:%M %p")
    overall_score = mental_scores.get('overall', 25)

    if report_type == 'iq':
        # IQ Cognitive Evaluation Report
        score_val = max(85, min(145, 90 + len(messages) * 10 + (overall_score // 5)))
        
        if score_val >= 120:
            cognitive_tier = "Superior Cognitive Performance"
            tier_badge = "bg-amber-500 text-white"
            summary = "User demonstrated exceptional pattern recognition, logical deduction, and abstract problem-solving under adaptive difficulty."
            strengths = [
                "Advanced numerical sequence deduction",
                "High logical pattern synthesis",
                "Rapid problem solving"
            ]
        elif score_val >= 100:
            cognitive_tier = "Above Average Logical Ability"
            tier_badge = "bg-teal-500 text-white"
            summary = "User showed strong analytical processing and consistent performance across Easy and Medium logic challenges."
            strengths = [
                "Good numerical sequence awareness",
                "Consistent deduction capacity"
            ]
        else:
            cognitive_tier = "Average Cognitive Profile"
            tier_badge = "bg-indigo-500 text-white"
            summary = "User completed foundational logic challenges with steady accuracy."
            strengths = [
                "Foundational logic pattern recognition"
            ]

        return {
            'report_type': 'iq',
            'title': 'IQ & Cognitive Assessment Report',
            'patient_name': user_name or "Test Candidate",
            'patient_email': user_email or "candidate@mindsense.ai",
            'date': formatted_date,
            'timestamp': now,
            'primary_mood': 'Focused',
            'estimated_iq_score': score_val,
            'cognitive_tier': cognitive_tier,
            'risk_badge': tier_badge,
            'scores': mental_scores,
            'summary': summary,
            'recommendations': strengths + [
                "Practice spatial logic and matrix reasoning puzzles weekly.",
                "Engage in analytical reading and mathematical problem solving."
            ],
            'total_session_messages': len(messages)
        }

    elif report_type == 'divorce':
        # Divorce Counseling Report
        if overall_score >= 60:
            conflict_intensity = "High Conflict Friction"
            conflict_badge = "bg-rose-500 text-white"
            summary = "Session evaluation indicates elevated emotional tension and communication friction during separation/divorce proceedings."
            key_insights = [
                "Emotional reactivity regarding asset/custody discussions.",
                "Communication breakdown requiring structured written boundaries."
            ]
            recommendations = [
                "Establish strict 24-hour cooling-off periods before responding to high-friction communications.",
                "Utilize BIFF (Brief, Informative, Friendly, Firm) communication rules.",
                "Engage a neutral professional mediator for dispute resolution.",
                "Protect children's emotional stability by prohibiting adult conflict in their presence."
            ]
        else:
            conflict_intensity = "Moderate / Constructive Transition"
            conflict_badge = "bg-teal-500 text-white"
            summary = "Session demonstrates productive emotional processing and willingness to establish healthy post-divorce boundaries."
            key_insights = [
                "Mutual commitment to child emotional stability.",
                "Constructive relationship transition."
            ]
            recommendations = [
                "Formalize a structured co-parenting calendar.",
                "Maintain individual counseling to process grief and personal transition.",
                "Practice daily mindfulness and stress management."
            ]

        return {
            'report_type': 'divorce',
            'title': 'Divorce & Relationship Counseling Report',
            'patient_name': user_name or "Client Partner",
            'patient_email': user_email or "client@mindsense.ai",
            'date': formatted_date,
            'timestamp': now,
            'primary_mood': emotion_stats.get('emotion', 'Stress'),
            'conflict_intensity': conflict_intensity,
            'risk_badge': conflict_badge,
            'scores': mental_scores,
            'summary': summary,
            'key_insights': key_insights,
            'recommendations': recommendations,
            'total_session_messages': len(messages)
        }

    else:
        # Standard Mental Health Report
        if overall_score >= 70:
            risk_level = "High"
            risk_badge = "bg-red-500 text-white"
            summary = "User displays elevated stress/anxiety requiring structured coping mechanisms and monitoring."
            recommendations = [
                "Practice progressive 5-4-3-2-1 sensory grounding techniques twice daily.",
                "Schedule regular breaks during work/study hours to alleviate cognitive load.",
                "Limit caffeine/stimulant intake in the evening hours.",
                "Consider reaching out to a professional mental health counselor for personalized therapy."
            ]
        elif overall_score >= 40:
            risk_level = "Moderate"
            risk_badge = "bg-amber-500 text-white"
            summary = "User experiences moderate emotional fluctuation and periodic stress pressures."
            recommendations = [
                "Incorporate 10-minute daily mindfulness breathing exercises.",
                "Maintain a daily mood journal to identify specific stress triggers.",
                "Engage in moderate physical exercise (e.g., 20-minute daily walks).",
                "Establish a consistent sleep hygiene routine."
            ]
        else:
            risk_level = "Low"
            risk_badge = "bg-emerald-500 text-white"
            summary = "User demonstrates stable emotional balance and healthy coping capacity."
            recommendations = [
                "Continue current positive wellness routines and active lifestyle.",
                "Maintain healthy social connections with friends and family.",
                "Practice periodic self-reflection and gratitude exercises."
            ]

        return {
            'report_type': 'mental',
            'title': 'Mental State Assessment & Counseling Report',
            'patient_name': user_name or "Guest User",
            'patient_email': user_email or "guest@mindsense.ai",
            'date': formatted_date,
            'timestamp': now,
            'primary_mood': emotion_stats.get('emotion', 'Calm'),
            'risk_level': risk_level,
            'risk_badge': risk_badge,
            'scores': mental_scores,
            'summary': summary,
            'recommendations': recommendations,
            'total_session_messages': len(messages)
        }
