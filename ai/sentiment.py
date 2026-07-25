import re

# Comprehensive Lexicon for 11 Emotion Categories
EMOTION_KEYWORDS = {
    'Happy': [
        'happy', 'joy', 'glad', 'excited', 'great', 'peaceful', 'hopeful',
        'calm', 'grateful', 'good', 'content', 'relaxed', 'wonderful', 'blessed',
        'cheerful', 'delighted', 'fantastic', 'awesome', 'smiling', 'going well'
    ],
    'Sad': [
        'sad', 'unhappy', 'upset', 'heartbroken', 'disappointed', 'grief',
        'down', 'gloomy', 'hurt', 'tears', 'crying', 'sorrow', 'mourning'
    ],
    'Stress': [
        'stressed', 'stress', 'overwhelmed', 'pressure', 'exhausted',
        'too much', 'burden', 'strained', 'busy', 'deadlines', 'hectic', 'swamped'
    ],
    'Anxiety': [
        'anxious', 'anxiety', 'worried', 'panic', 'nervous', 'scared',
        'restless', 'overthinking', 'heart racing', 'dread', 'uneasy', 'tense'
    ],
    'Anger': [
        'angry', 'mad', 'furious', 'annoyed', 'irritated', 'hate',
        'frustrated', 'rage', 'bitter', 'resentful', 'infuriated', 'pissed'
    ],
    'Fear': [
        'afraid', 'fear', 'terrified', 'frightened', 'scared', 'petrified',
        'horrified', 'phobic', 'intimidated', 'spooked'
    ],
    'Depression': [
        'depressed', 'depression', 'hopeless', 'empty', 'worthless',
        'giving up', 'numb', 'miserable', 'despair', 'darkness', 'meaningless'
    ],
    'Loneliness': [
        'lonely', 'alone', 'isolated', 'abandoned', 'rejected', 'nobody',
        'disconnected', 'left out', 'companionless', 'solitary'
    ],
    'Confusion': [
        'confused', 'lost', 'uncertain', 'puzzled', 'mixed signals',
        'dont know', 'don\'t know', 'unclear', 'confusing', 'undecided', 'stuck'
    ],
    'Burnout': [
        'burnout', 'burnt out', 'drained', 'empty tank', 'no energy',
        'physically exhausted', 'mentally exhausted', 'cannot go on', 'can\'t go on'
    ]
}

def analyze_sentiment_and_emotion(text):
    """
    Detect user emotion across 11 categories:
    Happy, Sad, Stress, Anxiety, Anger, Fear, Depression, Loneliness, Confusion, Burnout, Neutral.
    Calculates positive/negative/neutral percentages and mental scores.
    """
    if not text:
        return {
            'emotion': 'Neutral',
            'sentiment': {'positive': 33, 'negative': 33, 'neutral': 34},
            'scores': {'stress': 10, 'anxiety': 10, 'depression': 10, 'overall': 10}
        }

    lower_text = text.lower()

    emotion_counts = {emotion: 0 for emotion in EMOTION_KEYWORDS}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower_text:
                matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', lower_text))
                emotion_counts[emotion] += (matches if matches > 0 else 1)

    # Determine primary emotion
    sorted_emotions = sorted(emotion_counts.items(), key=lambda item: item[1], reverse=True)
    primary_emotion = sorted_emotions[0][0] if sorted_emotions[0][1] > 0 else 'Neutral'

    # Compute score metrics (0-100)
    stress_score = min(100, (emotion_counts['Stress'] + emotion_counts['Burnout']) * 35 + emotion_counts['Anxiety'] * 15 + 15)
    anxiety_score = min(100, emotion_counts['Anxiety'] * 40 + (emotion_counts['Fear'] + emotion_counts['Confusion']) * 20 + 10)
    depression_score = min(100, (emotion_counts['Depression'] + emotion_counts['Loneliness']) * 45 + emotion_counts['Sad'] * 20 + 10)
    overall_mental_score = round((stress_score + anxiety_score + depression_score) / 3)

    pos_score = emotion_counts['Happy']
    neg_score = sum(count for em, count in emotion_counts.items() if em != 'Happy')

    if pos_score > neg_score:
        positive_pct = min(95, 60 + pos_score * 15)
        negative_pct = max(5, 100 - positive_pct - 10)
        neutral_pct = 100 - positive_pct - negative_pct
    elif neg_score > 0:
        negative_pct = min(85, 45 + neg_score * 15)
        positive_pct = max(5, 100 - negative_pct - 15)
        neutral_pct = 100 - positive_pct - negative_pct
    else:
        positive_pct = 20
        negative_pct = 10
        neutral_pct = 70

    return {
        'emotion': primary_emotion,
        'sentiment': {
            'positive': round(positive_pct),
            'negative': round(negative_pct),
            'neutral': round(neutral_pct)
        },
        'scores': {
            'stress': round(stress_score),
            'anxiety': round(anxiety_score),
            'depression': round(depression_score),
            'overall': round(overall_mental_score)
        }
    }
