import json
import random
import re
import time
from config import Config
from ai.iq_questions import get_fallback_iq_batch

try:
    import json_repair
except ImportError:
    json_repair = None

def _extract_json_array(raw_text):
    """
    Safely extracts and parses a JSON array from a raw LLM response.
    Strips markdown blocks and extracts between first '[' and last ']'.
    """
    cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()

    first_bracket = cleaned_text.find('[')
    last_bracket = cleaned_text.rfind(']')

    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        cleaned_text = cleaned_text[first_bracket:last_bracket+1]

    # 1. Try json_repair first if available
    if json_repair is not None:
        try:
            parsed = json_repair.loads(cleaned_text)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    # 2. Standard json.loads
    try:
        return json.loads(cleaned_text)
    except Exception:
        # Regex clean trailing commas before closing braces
        cleaned_text = re.sub(r',\s*\]', ']', cleaned_text)
        cleaned_text = re.sub(r',\s*\}', '}', cleaned_text)
        try:
            return json.loads(cleaned_text)
        except Exception as final_err:
            if json_repair is not None:
                try:
                    return json_repair.loads(cleaned_text)
                except Exception:
                    pass
            raise ValueError(f"Failed to parse JSON array from output: {final_err}")

def generate_iq_test_batch():
    """
    Dynamically generates a full 20-question IQ test via Groq API.
    Features:
    - Multi-model fallback cascade (70B -> 8B-instant -> backup)
    - Exponential backoff on rate limits / 429 errors
    - Request timeouts to avoid hanging on slow network
    - Seamless fallback to authentic psychometric question bank if all API calls fail
    """
    api_key = Config.GROQ_API_KEY
    if not api_key or api_key.startswith("gsk_placeholder"):
        print("[IQ Generator] No valid Groq API key found. Using balanced question bank fallback.")
        return get_fallback_iq_batch()

    # Model priority cascade: Try configured primary, fallback models
    primary_model = Config.GROQ_MODEL
    fallback_model = getattr(Config, 'GROQ_FALLBACK_MODEL', 'llama-3.3-70b-versatile')
    models_to_try = []
    for m in [primary_model, fallback_model, "qwen/qwen3.8-27b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "allam-2-7b"]:
        if m and m not in models_to_try:
            models_to_try.append(m)

    timeout_sec = getattr(Config, 'GROQ_TIMEOUT', 25)

    try:
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert psychometrician. Output exactly 20 unique psychometric questions in a strict JSON array. No markdown, no explanations outside JSON."),
            ("human", """
Generate a JSON array of exactly 20 unique IQ test questions:
- Questions 1 to 7: EASY (Number series, simple analogies)
- Questions 8 to 14: MEDIUM (Pattern logic, 2-step sequences, deduction)
- Questions 15 to 20: HARD (Abstract logic, spatial math, complex series)

Each object must follow this exact JSON structure:
[
  {{
    "category": "Numerical Reasoning",
    "question": "Clear question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Exact text of the correct option",
    "explanation": "Concise logical rationale"
  }}
]
""")
        ])

        messages = prompt.format_messages()
        data = None

        for model_idx, model_name in enumerate(models_to_try):
            print(f"[IQ Generator] Attempting batch generation with model: {model_name}")
            max_attempts = 2

            for attempt in range(max_attempts):
                try:
                    llm = ChatGroq(
                        groq_api_key=api_key,
                        model_name=model_name,
                        temperature=0.7,
                        max_tokens=3000,
                        request_timeout=timeout_sec
                    )

                    response = llm.invoke(messages)
                    raw_output = response.content if hasattr(response, 'content') else str(response)

                    parsed_list = _extract_json_array(raw_output)
                    if isinstance(parsed_list, list) and len(parsed_list) >= 5:
                        data = parsed_list
                        print(f"[IQ Generator] Successfully parsed {len(data)} questions using {model_name}!")
                        break

                except Exception as call_err:
                    err_str = str(call_err).lower()
                    print(f"[IQ Generator Retry {attempt+1}/{max_attempts} on {model_name}] Warning: {call_err}")

                    is_model_not_found = "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str
                    # If rate limit (429) or high demand (503), apply exponential backoff
                    if "rate limit" in err_str or "429" in err_str or "high demand" in err_str or "capacity" in err_str:
                        backoff = (2.0 ** attempt) + random.uniform(0.3, 0.7)
                        print(f"[IQ Generator] Rate limit detected. Backing off for {backoff:.2f}s...")
                        time.sleep(backoff)
                    elif is_model_not_found:
                        print(f"[IQ Generator Failover] Model {model_name} not available. Fast-failing over to next model...")
                        break
                    else:
                        time.sleep(0.5)

            if data is not None:
                break

        # If LLM generation succeeded with valid list
        if data and isinstance(data, list) and len(data) >= 5:
            formatted_questions = []
            for idx, q in enumerate(data[:20]):
                difficulty = 'easy' if idx < 7 else ('medium' if idx < 14 else 'hard')
                formatted_questions.append({
                    'id': f"ai_{difficulty}_{random.randint(10000, 99999)}",
                    'difficulty': difficulty,
                    'category': q.get('category', 'Logical Reasoning'),
                    'question': q.get('question', 'Identify the next logical term in this pattern.'),
                    'options': q.get('options', ['A', 'B', 'C', 'D']),
                    'answer': q.get('answer', 'A'),
                    'explanation': q.get('explanation', 'Logical analysis of the given sequence.')
                })

            # If fewer than 20 returned by LLM, pad remaining with bank questions
            if len(formatted_questions) < 20:
                needed = 20 - len(formatted_questions)
                pad_pool = get_fallback_iq_batch()
                formatted_questions.extend(pad_pool[:needed])

            return formatted_questions

    except Exception as outer_err:
        print(f"[IQ Generator Error] Unexpected generation failure: {outer_err}")

    # Seamless fallback: Guarantee a functioning test regardless of API conditions
    print("[IQ Generator] Serving randomized 20-question psychometric bank fallback.")
    return get_fallback_iq_batch()
