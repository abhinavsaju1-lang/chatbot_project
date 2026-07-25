import os
import re
import random
from difflib import SequenceMatcher
from config import Config
from rag.retriever import get_relevant_context
from ai.prompt import get_prompt_for_mode, RESPONSE_STYLES
from ai.sentiment import analyze_sentiment_and_emotion

# ============================================================
# BLACKLISTED OPENINGS — phrases the AI must never start with
# ============================================================
BLACKLISTED_OPENINGS = [
    "i hear you",
    "i understand",
    "i'm here for you",
    "i am here for you",
    "thank you for sharing",
    "it sounds like",
    "i can imagine",
    "i can see that",
    "that must be",
]

# ============================================================
# INTENT DETECTION — 12 clinical intent categories
# ============================================================
def detect_user_intent(text):
    """Detect specific user intent from conversation input using word boundaries."""
    if not text:
        return 'General'
    lower_text = text.lower()

    def has_keyword(keywords):
        return any(re.search(r'\b' + re.escape(k) + r'\b', lower_text) for k in keywords)

    # Check Grief first
    if has_keyword(['grief', 'passed away', 'died', 'loss', 'funeral', 'miss them', 'death']):
        return 'Grief'
    elif has_keyword(['internship', 'promotion', 'won', 'got a job', 'achievement', 'success', 'accepted', 'hired', 'selected', 'passed the exam', 'passed my exam', 'cleared the']):
        return 'Achievement'
    elif has_keyword(['exam', 'failed', 'test', 'flunked', 'grade', 'score', 'result']):
        return 'Exam Failure'
    elif has_keyword(['trust', "doesn't trust", 'wife', 'husband', 'partner', 'cheated', 'betrayed', 'lying']):
        return 'Trust Issue'
    elif has_keyword(['argue', 'arguing', 'fight', 'fighting', 'disagree', 'yelling', 'shouting']):
        return 'Relationship Argument'
    elif has_keyword(['misunderstand', 'misunderstanding', 'interpret', 'communication']):
        return 'Misunderstanding'
    elif has_keyword(['sleep', 'insomnia', 'nightmare', 'awake', "can't sleep", 'no sleep']):
        return 'Sleep Issues'
    elif has_keyword(['lonely', 'alone', 'isolated', 'no friends', 'nobody']):
        return 'Loneliness'
    elif has_keyword(['burnout', 'burnt out', 'exhausted', 'drained', 'no energy', 'overworked']):
        return 'Burnout'
    elif has_keyword(['anxious', 'anxiety', 'panic', 'overthinking', 'worried', 'nervous']):
        return 'Anxiety'
    elif has_keyword(['happy', 'great', 'awesome', 'wonderful', 'excited', 'good day', 'amazing', 'fantastic', 'cheerful']):
        return 'Positive Emotion'
    elif has_keyword(['sad', 'depressed', 'hopeless', 'cry', 'tears', 'miserable', 'empty']):
        return 'Sadness'
    
    return 'General'


# ============================================================
# DYNAMIC WORD BOUND CALCULATION
# ============================================================
def determine_target_word_bounds(input_text):
    """Calculate target min/max word count based on user input length."""
    word_count = len(input_text.split()) if input_text else 0
    if word_count < 15:
        return 20, 55, "20–55 WORDS (Short & Direct)"
    elif word_count <= 40:
        return 55, 100, "55–100 WORDS (Medium)"
    else:
        return 100, 150, "100–150 WORDS MAXIMUM"


# ============================================================
# SENTENCE-BOUNDARY TRUNCATION
# ============================================================
def truncate_to_word_limit(text, max_words=150):
    """Cleanly truncate text to fit within max_words at sentence boundaries."""
    if not text:
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    selected, current_count = [], 0
    for s in sentences:
        wc = len(s.split())
        if current_count + wc <= max_words:
            selected.append(s)
            current_count += wc
        else:
            break
    return " ".join(selected) if selected else " ".join(sentences[:2])


# ============================================================
# SEMANTIC SIMILARITY CHECK (anti-repetition)
# ============================================================
def is_too_similar_to_history(new_response, past_responses, threshold=0.60):
    """Return True if new_response is semantically too close to any past response."""
    new_lower = new_response.lower()
    for past in past_responses:
        ratio = SequenceMatcher(None, new_lower, past.lower()).ratio()
        if ratio >= threshold:
            return True
    return False


# ============================================================
# MAIN CHATBOT CLASS
# ============================================================
class MindSenseChatbot:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.model_name = Config.GROQ_MODEL
        self.llm = None

        if self.api_key and not self.api_key.startswith("gsk_placeholder"):
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    groq_api_key=self.api_key,
                    model_name=self.model_name,
                    temperature=0.85,
                    top_p=0.92,
                    max_tokens=320
                )
                print(f"[ChatGroq] MindSense Production Counselor Engine Initialized — {self.model_name}")
            except Exception as e:
                print(f"[ChatGroq Warning] Could not initialize ChatGroq: {e}")

    def generate_response(self, user_input, mode='mental', history_list=None, iq_level=1, past_bot_responses=None):
        """
        Generates a context-aware, intent-driven, non-repetitive counseling response.

        Anti-repetition strategy:
        1. Tracks past 7 bot responses in memory window.
        2. Compares new response against history with SequenceMatcher (threshold 60%).
        3. Retries up to 3 times with increasing temperature if too similar.
        4. Strips blacklisted opening phrases.
        5. Enforces dynamic word limit at sentence boundaries.
        """
        history_list = history_list or []
        past_bot_responses = past_bot_responses or []

        # ── 1. INTENT, EMOTION & WORD BOUND DETERMINATION ──────────────────
        detected_intent = detect_user_intent(user_input)
        sentiment_analysis = analyze_sentiment_and_emotion(user_input)
        detected_emotion = sentiment_analysis['emotion']
        min_words, max_words, word_range_str = determine_target_word_bounds(user_input)

        # ── 2. FORMAT LAST 6 SESSION TURNS AS DIALOGUE CONTEXT ─────────────
        formatted_history = []
        for turn in history_list[-6:]:
            u_msg = turn.get('user', turn.get('message', ''))
            # Check 'bot_response' (used by active session) and 'bot' (used by DB load)
            b_msg = turn.get('bot_response', turn.get('bot', turn.get('response', '')))
            if u_msg and b_msg:
                formatted_history.append(f"User: {u_msg}\nCounselor: {b_msg}")
        chat_history_str = "\n\n".join(formatted_history) if formatted_history else "This is the opening turn of the session."

        # ── 3. RAG CONTEXT RETRIEVAL (mental & divorce only) ────────────────
        context = ""
        if mode in ['mental', 'divorce']:
            try:
                context = get_relevant_context(user_input)
            except Exception:
                context = ""

        # ── 4. LLM GENERATION WITH ANTI-REPETITION RETRY LOOP ──────────────
        bot_reply = None
        last_candidate = None  # Track last LLM output even if similarity check fails

        if self.llm and mode != 'iq':
            prompt_template = get_prompt_for_mode(mode)
            base_prompt = {
                'response_style': random.choice(RESPONSE_STYLES),
                'target_word_range': word_range_str,
                'user_intent': detected_intent,
                'detected_emotion': detected_emotion,
                'context': context or "Use empathy, active listening, and evidence-based counseling.",
                'chat_history': chat_history_str,
                'user_input': user_input
            }

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Format as true [SystemMessage, HumanMessage] sequence
                    messages = prompt_template.format_messages(**base_prompt)
                    
                    # Increase temperature on each retry to force more diversity
                    if attempt > 0:
                        from langchain_groq import ChatGroq
                        retry_llm = ChatGroq(
                            groq_api_key=self.api_key,
                            model_name=self.model_name,
                            temperature=min(1.0, 0.85 + attempt * 0.08),
                            top_p=0.95,
                            max_tokens=320
                        )
                        response = retry_llm.invoke(messages)
                    else:
                        response = self.llm.invoke(messages)

                    raw_reply = response.content if hasattr(response, 'content') else str(response)
                    last_candidate = self._clean_response(raw_reply, max_words)

                    if not is_too_similar_to_history(last_candidate, past_bot_responses[-7:]):
                        bot_reply = last_candidate
                        break
                    else:
                        print(f"[Anti-Repetition] Attempt {attempt + 1}: too similar, retrying...")

                except Exception as e:
                    print(f"[LLM Error] Attempt {attempt + 1}: {e}")

            # Always prefer the LLM's last output
            if not bot_reply and last_candidate:
                bot_reply = last_candidate

        # ── 5. FALLBACK (Only if LLM completely crashes) ────────
        if not bot_reply:
            bot_reply = "I'm having a bit of trouble processing right now, but I want to make sure I understand. Could you share that with me again?"

        return {
            'bot_response': bot_reply,
            'mode': mode,
            'intent': detected_intent,
            'emotion': detected_emotion,
            'sentiment': sentiment_analysis,
            'context_used': context
        }

    def _clean_response(self, raw_reply, max_words):
        """
        Cleans raw LLM output:
        1. Strips blacklisted opening phrases.
        2. Enforces max word limit at sentence boundaries.
        3. Capitalizes first letter after stripping.
        """
        if not raw_reply:
            return ""

        cleaned = raw_reply.strip()

        # Remove any role-prefix artifacts (e.g., "Counselor:", "Therapist:")
        cleaned = re.sub(r'^(Counselor|Therapist|MindSense[- ]?AI|Assistant)\s*:\s*', '', cleaned, flags=re.IGNORECASE).strip()

        # Strip blacklisted openings
        lower_c = cleaned.lower()
        for bp in BLACKLISTED_OPENINGS:
            if lower_c.startswith(bp):
                pattern = re.escape(bp)
                cleaned = re.sub(r'^' + pattern + r'[,.\s!\-]*', '', cleaned, flags=re.IGNORECASE).strip()
                if cleaned and cleaned[0].islower():
                    cleaned = cleaned[0].upper() + cleaned[1:]
                break

        # Enforce word limit
        cleaned = truncate_to_word_limit(cleaned, max_words=max_words)
        return cleaned


# ── Global Singleton ────────────────────────────────────────────────────────
chatbot_instance = MindSenseChatbot()


def get_chatbot_response(user_input, mode='mental', history_list=None, iq_level=1, past_bot_responses=None):
    return chatbot_instance.generate_response(
        user_input, mode=mode, history_list=history_list,
        iq_level=iq_level, past_bot_responses=past_bot_responses
    )
