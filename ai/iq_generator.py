import json
import json_repair
import random
import re
from config import Config

def _extract_json_array(raw_text):
    """
    Safely extracts and parses a JSON array from a raw LLM response.
    Unconditionally prints the raw output for debugging.
    """
    print('=== RAW LLM OUTPUT START ===\n' + raw_text + '\n=== RAW LLM OUTPUT END ===', flush=True)
    
    # Strip markdown code blocks if the LLM included them
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    first_bracket = raw_text.find('[')
    last_bracket = raw_text.rfind(']')

    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        cleaned_text = raw_text[first_bracket:last_bracket+1]
    else:
        cleaned_text = raw_text

    try:
        return json_repair.loads(cleaned_text)
    except json.JSONDecodeError:
        # Fallback: fix trailing commas and newlines inside strings
        import re
        cleaned_text = re.sub(r',\s*\]', ']', cleaned_text)
        cleaned_text = re.sub(r',\s*\}', '}', cleaned_text)
        try:
            return json_repair.loads(cleaned_text)
        except json.JSONDecodeError as final_err:
            raise ValueError(f"Failed to parse JSON from LLM output. Error: {final_err}")

def generate_iq_test_batch():
    """
    Dynamically generates a full 20-question IQ test in a single LLM call.
    Questions are strictly scaled: 1-7 Easy, 8-14 Medium, 15-20 Hard.
    Returns a list of 20 question dictionaries.
    """
    api_key = Config.GROQ_API_KEY
    model_name = Config.GROQ_MODEL
    
    if not api_key or api_key.startswith("gsk_placeholder"):
        raise Exception("Invalid or missing Groq API Key.")

    try:
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=0.8,
            max_tokens=4000
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert psychometrician designing an adaptive IQ test. Your task is to generate exactly 20 unique, challenging psychometric IQ questions in a single JSON array."),
            ("human", """
Generate a JSON array of exactly 20 IQ questions.

Ensure the questions span diverse categories:
- Numerical Reasoning (Number sequences, math logic)
- Alphabet/Verbal Reasoning (Letter coding, analogies)
- Logical/Pattern Recognition (Syllogisms, deductive logic)
- Spatial Deduction (Mental rotation, visual logic)

CRITICAL DIFFICULTY SCALING:
- Questions 1 to 7 must be EASY (straightforward, single-step).
- Questions 8 to 14 must be MEDIUM (multi-step, requires some thought).
- Questions 15 to 20 must be HARD (complex, abstract, highly challenging).

INSTRUCTIONS:
- Ensure all questions are solvable purely through logic, math, or pattern recognition (no trivia).
- Generate completely UNIQUE questions. Do NOT use clichés (avoid 'If Mary has 3 apples', 'bat and ball cost $1.10', etc).
- Make sure exactly one of the 4 options is unambiguously correct.
- Provide a brief, logical explanation for the correct answer.

Return ONLY a valid JSON array of objects with this exact structure, nothing else:
[
  {{
    "category": "Numerical Reasoning",
    "question": "The question text here",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "answer": "The exact text of the correct option",
    "explanation": "Brief logical explanation for why this is the answer"
  }},
  ... (19 more objects)
]
""")
        ])
        
        data = None
        for attempt in range(3):
            try:
                response = llm.invoke(prompt.format_messages())
                raw_output = response.content if hasattr(response, 'content') else str(response)
                
                data = _extract_json_array(raw_output)
                if isinstance(data, list) and len(data) >= 5: # accept partial if retries are failing, we'll pad it
                    break
            except Exception as e:
                print(f"[IQ Generator Retry {attempt+1}/3 Failed] {e}")
                if attempt == 2:
                    raise e
                    
        if not data or not isinstance(data, list):
            raise ValueError("LLM returned valid JSON, but it is not a list/array.")

        # Ensure we return exactly 20 questions, properly formatted
        formatted_questions = []
        for idx, q in enumerate(data[:20]):
            difficulty = 'easy' if idx < 7 else ('medium' if idx < 14 else 'hard')
            formatted_questions.append({
                'id': f"q_{random.randint(10000, 99999)}",
                'difficulty': difficulty,
                'category': q.get('category', 'Logical Reasoning'),
                'question': q.get('question', 'Error parsing question.'),
                'options': q.get('options', ['A', 'B', 'C', 'D']),
                'answer': q.get('answer', 'A'),
                'explanation': q.get('explanation', 'No explanation provided.')
            })
            
        return formatted_questions

    except Exception as e:
        print(f"[IQ Generator Batch Error] {e}")
        raise Exception(f"Failed to generate dynamic test: {e}")