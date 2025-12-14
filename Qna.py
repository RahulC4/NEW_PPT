# llm/qna_engine.py

from llm.llm_utils import chat_completion
from utils import logger

SYSTEM_PROMPT = """
You are a smart assistant that generates clear, business-friendly questions
for collecting required information needed to build a presentation.

Rules:
- Input will contain required_fields from the presentation planner.
- For each field, generate one clear question.
- Questions must be simple and easy to answer.
- Return valid JSON ONLY.
- Do NOT create content—only create QUESTIONS.
"""

def generate_questions(plan: dict):
    """
    Takes the presentation plan and returns a list of questions to ask the user.
    """

    required_fields = []
    for slide in plan.get("slides", []):
        for field in slide.get("required_fields", []):
            required_fields.append(field)

    required_fields = list(dict.fromkeys(required_fields))  # dedupe

    USER_PROMPT = f"""
    Required fields: {required_fields}

    Return JSON:
    {{
        "questions": [
            {{ "field": "project_name", "question": "What is the project name?" }},
            {{ "field": "client_name", "question": "Who is the client?" }}
        ]
    }}
    """

    result = chat_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        json_mode=True
    )

    if not result or "questions" not in result:
        logger.error("Question generation failed.")
        return {"questions": []}

    return result



# -------------------------------------------------------
# COLLECT USER ANSWERS & BUILD FINAL CONTENT PROFILE
# -------------------------------------------------------
def build_content_profile(plan: dict, user_answers: dict):
    """
    Returns a normalized JSON object used for slide content generation.

    Example:
        user_answers = {
            "project_name": "Claims Modernization",
            "client_name": "CareSource",
            ...
        }
    """

    profile = {
        "goal": plan.get("goal", ""),
        "fields": {},
        "slides": plan.get("slides", [])
    }

    for slide in plan.get("slides", []):
        for field in slide.get("required_fields", []):
            profile["fields"][field] = user_answers.get(field, "")

    return profile
