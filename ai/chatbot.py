import os
import re
import time
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
# CRISIS & SELF-HARM SAFETY PROTOCOL
# ============================================================
CRISIS_TRIGGERS = [
    r'\bsuicid(e|al|ing)?\b',
    r'\bkill(ing)?\s+(my\s*self|me)\b',
    r'\bself[- ]?harm(ing)?\b',
    r'\b(harm|hurt)(ing)?\s+my\s*self\b',
    r'\bend(ing)?\s+(my\s*life|it\s*all)\b',
    r'\b(want|wanna)\s+to\s+die\b',
    r'\bwish\s+(i\s*was|i\s*were)\s+dead\b',
    r'\bbetter\s+off\s+dead\b',
    r'\btake\s+my\s+(own\s+)?life\b',
    r'\b(slit|cut)\s+(my\s*wrist|my\s*wrists|my\s*throat)\b',
    r'\bhang\s+my\s*self\b',
    r'\boverdose\b',
    r'\b(no\s+reason\s+to\s+live|don\'?t\s+want\s+to\s+live)\b',
    r'\b(can\'?t|cannot)\s+go\s+on\s+living\b'
]

def is_crisis_intent(text):
    """Detect acute crisis, suicide, or self-harm triggers from user input."""
    if not text:
        return False
    lower_text = text.lower()
    for pattern in CRISIS_TRIGGERS:
        if re.search(pattern, lower_text):
            return True
    return False

def get_crisis_response(user_name='there'):
    """Return a warm, urgent, non-judgmental crisis intervention message with 24/7 helplines."""
    name_salutation = f", {user_name}" if user_name and user_name != 'Guest User' else ""
    return (
        f"I can hear how much pain and distress you are carrying right now{name_salutation}, but please know that you do not have to walk through this alone. Your life has immense value, and there is compassionate, confidential help available right now.\n\n"
        "Please connect immediately with someone trained and ready to support you through this moment:\n\n"
        "• **Tele-MANAS (24/7 National Mental Health Helpline, Toll-Free):** **14416** or **1800-891-4416**\n"
        "• **KIRAN Mental Health Helpline (Govt of India, 24/7):** **1800-599-0019**\n"
        "• **Vandrevala Foundation (24/7 Free Helpline & WhatsApp):** **+91 9999 666 555**\n"
        "• **National Emergency Services:** **112** (Police & Medical Emergency)\n"
        "• **International / Global Support:** Call or text **988** (US/Canada), or visit **findahelpline.com** for free, confidential crisis support in your country.\n\n"
        "Please reach out to one of these services right now, or contact a trusted friend, family member, or healthcare professional. Please stay safe — I am here with you, and there is help available."
    )

# ============================================================
# INTENT DETECTION — 13 clinical intent categories
# ============================================================
def detect_user_intent(text):
    """Detect specific user intent from conversation input using word boundaries."""
    if not text:
        return 'General'
    lower_text = text.lower()

    # 1. Immediate Crisis / Self-Harm check
    if is_crisis_intent(text):
        return 'Crisis'

    def has_keyword(keywords):
        return any(re.search(r'\b' + re.escape(k) + r'\b', lower_text) for k in keywords)

    # Check Profile Query
    if has_keyword(['gender', 'who am i', 'my name', 'my profile', 'my account', 'my email']) or \
       any(p in lower_text for p in ['what is my gender', "what's my gender", 'whats my gender', 'what is my name', "what's my name", 'whats my name', 'who am i', 'what is my email', 'my registered gender']):
        return 'Profile Query'

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
        self.fallback_model = getattr(Config, 'GROQ_FALLBACK_MODEL', 'llama-3.1-8b-instant')
        self.request_timeout = getattr(Config, 'GROQ_TIMEOUT', 25)
        self.llm = None

        if self.api_key and not self.api_key.startswith("gsk_placeholder"):
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    groq_api_key=self.api_key,
                    model_name=self.model_name,
                    temperature=0.85,
                    max_tokens=320,
                    request_timeout=self.request_timeout,
                    model_kwargs={"top_p": 0.92}
                )
                print(f"[ChatGroq] MindSense Production Counselor Engine Initialized — {self.model_name} (fallback: {self.fallback_model})")
            except Exception as e:
                print(f"[ChatGroq Warning] Could not initialize ChatGroq: {e}")

    def generate_response(self, user_input, mode='mental', history_list=None, iq_level=1, past_bot_responses=None, user_gender='Prefer not to say', user_name='Guest User', user_email='guest@mindsense.ai', **kwargs):
        """
        Generates a context-aware, intent-driven, non-repetitive counseling response.

        Anti-repetition & High-Availability strategy:
        1. Injects dynamic user profile details (Name, Gender, Email) into LLM system prompt.
        2. Tracks past 7 bot responses in memory window.
        3. Compares new response against history with SequenceMatcher (threshold 60%).
        4. Cascades through fallback models (70B -> 8B-instant) on rate limit / capacity errors.
        5. Applies exponential backoff with jitter on 429/503 errors.
        6. Strips blacklisted opening phrases.
        7. Enforces dynamic word limit at sentence boundaries.
        8. Returns warm, mode-specific empathetic fallback if API is unreachable.
        """
        history_list = history_list or []
        past_bot_responses = past_bot_responses or []
        user_name = kwargs.get('user_name', user_name) or 'Guest User'
        user_gender = kwargs.get('user_gender', user_gender) or 'Prefer not to say'
        user_email = kwargs.get('user_email', user_email) or 'guest@mindsense.ai'

        # ── 1. INTENT, EMOTION & WORD BOUND DETERMINATION ──────────────────
        detected_intent = detect_user_intent(user_input)

        # ── IMMEDIATE CRISIS INTERVENTION OVERRIDE ─────────────────────────
        if detected_intent == 'Crisis' or is_crisis_intent(user_input):
            crisis_reply = get_crisis_response(user_name=user_name)
            return {
                'bot_response': crisis_reply,
                'mode': mode,
                'intent': 'Crisis',
                'emotion': 'High Risk',
                'sentiment': {
                    'emotion': 'High Risk',
                    'sentiment': {'positive': 0, 'negative': 95, 'neutral': 5},
                    'scores': {'stress': 95, 'anxiety': 95, 'depression': 95, 'overall': 95}
                },
                'context_used': 'Crisis Intervention Protocol Triggered'
            }

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

        # ── 4. LLM GENERATION WITH CASCADE & ANTI-REPETITION RETRY LOOP ────
        bot_reply = None
        last_candidate = None  # Track last LLM output even if similarity check fails

        if self.api_key and not self.api_key.startswith("gsk_placeholder") and mode != 'iq':
            prompt_template = get_prompt_for_mode(mode)
            base_prompt = {
                'user_name': user_name,
                'user_gender': user_gender,
                'user_email': user_email,
                'response_style': random.choice(RESPONSE_STYLES),
                'target_word_range': word_range_str,
                'user_intent': detected_intent,
                'detected_emotion': detected_emotion,
                'context': context or "Use empathy, active listening, and evidence-based counseling.",
                'chat_history': chat_history_str,
                'user_input': user_input
            }

            candidate_models = [self.model_name]
            if self.fallback_model and self.fallback_model not in candidate_models:
                candidate_models.append(self.fallback_model)
            if "llama-3.1-8b-instant" not in candidate_models:
                candidate_models.append("llama-3.1-8b-instant")

            max_retries = 3

            for attempt in range(max_retries):
                target_model = candidate_models[min(attempt, len(candidate_models) - 1)]
                try:
                    messages = prompt_template.format_messages(**base_prompt)
                    
                    from langchain_groq import ChatGroq
                    temp = min(1.0, 0.85 + attempt * 0.05)

                    if attempt == 0 and self.llm and target_model == self.model_name:
                        response = self.llm.invoke(messages)
                    else:
                        active_llm = ChatGroq(
                            groq_api_key=self.api_key,
                            model_name=target_model,
                            temperature=temp,
                            max_tokens=320,
                            request_timeout=self.request_timeout,
                            model_kwargs={"top_p": 0.95}
                        )
                        response = active_llm.invoke(messages)

                    raw_reply = response.content if hasattr(response, 'content') else str(response)
                    last_candidate = self._clean_response(raw_reply, max_words)

                    if not is_too_similar_to_history(last_candidate, past_bot_responses[-7:]):
                        bot_reply = last_candidate
                        break
                    else:
                        print(f"[Anti-Repetition] Attempt {attempt + 1}: too similar, retrying...")

                except Exception as e:
                    err_str = str(e).lower()
                    print(f"[LLM Error] Attempt {attempt + 1} ({target_model}): {e}")

                    # Check for rate limits or high-demand / capacity errors
                    is_rate_limit = any(term in err_str for term in ['429', 'rate_limit', 'capacity', '503', 'resource_exhausted', 'tokens per minute', 'tpm'])
                    if attempt < max_retries - 1:
                        backoff_sec = (1.5 ** attempt) + random.uniform(0.2, 0.5)
                        if is_rate_limit:
                            next_model = candidate_models[min(attempt + 1, len(candidate_models) - 1)]
                            print(f"[ChatGroq Backoff] Rate limit or high capacity detected. Backing off {backoff_sec:.2f}s and cascading to {next_model}...")
                        time.sleep(backoff_sec)

            # Always prefer the LLM's last output if valid
            if not bot_reply and last_candidate:
                bot_reply = last_candidate

        # ── 5. EMPATHETIC MODE FALLBACK (If LLM is completely unreachable) ──
        if not bot_reply:
            bot_reply = self._get_mode_fallback(mode, user_input, detected_intent, detected_emotion, user_name=user_name, user_gender=user_gender)

        return {
            'bot_response': bot_reply,
            'mode': mode,
            'intent': detected_intent,
            'emotion': detected_emotion,
            'sentiment': sentiment_analysis,
            'context_used': context
        }

    def _get_mode_fallback(self, mode, user_input, detected_intent, detected_emotion, user_name='Guest User', user_gender='Prefer not to say'):
        """Provide a supportive, mode-specific empathetic fallback, crisis guidance, or direct profile answer if LLM capacity is unavailable."""
        lower_input = (user_input or '').lower()
        if detected_intent == 'Crisis' or is_crisis_intent(user_input):
            return get_crisis_response(user_name=user_name)

        if detected_intent == 'Profile Query' or any(k in lower_input for k in ['gender', 'my name', 'who am i', 'my profile', 'my account', 'my email', 'whats my', 'what is my']):
            gender_display = user_gender if user_gender and user_gender.strip() else 'Prefer not to say'
            name_display = user_name if user_name and user_name.strip() else 'Guest User'
            if 'gender' in lower_input:
                return f"According to your profile, your registered gender is {gender_display}."
            elif 'name' in lower_input or 'who am i' in lower_input:
                return f"According to your profile, your name is {name_display}."
            else:
                return f"According to your profile, your name is {name_display} and your registered gender is {gender_display}."

        if mode == 'divorce':
            return (
                "Going through relationship challenges or divorce can feel emotionally overwhelming and draining. "
                "I am here to support you without judgment. Take a gentle breath, and whenever you're ready, "
                "tell me what feels heaviest on your mind right now."
            )
        elif mode == 'mental':
            return (
                "I'm here with you, and what you're experiencing is important. Sometimes taking a pause and a slow breath can help center us. "
                "Whenever you feel ready, please share what feels most overwhelming or on your mind today."
            )
        else:
            return (
                "I hear how important this is to you, and I want to support you through it. "
                "Please take your time, and tell me a bit more about what you're going through."
            )

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


def get_chatbot_response(user_input, mode='mental', history_list=None, iq_level=1, past_bot_responses=None, user_gender='Prefer not to say', user_name='Guest User', user_email='guest@mindsense.ai', **kwargs):
    u_name = kwargs.get('user_name', user_name)
    u_gender = kwargs.get('user_gender', user_gender)
    u_email = kwargs.get('user_email', user_email)
    return chatbot_instance.generate_response(
        user_input, mode=mode, history_list=history_list,
        iq_level=iq_level, past_bot_responses=past_bot_responses,
        user_gender=u_gender, user_name=u_name, user_email=u_email
    )
