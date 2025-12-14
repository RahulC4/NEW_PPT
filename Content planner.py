# llm/content_planner.py

from llm.llm_utils import chat_completion
from utils import logger

SYSTEM_PROMPT = """
You are an expert presentation architect.
Given a user prompt, you must produce a structured plan for a complete professional presentation.

Your output MUST be valid JSON only.

Rules:
- Identify the goal of the presentation.
- Map it to standard proposal deck sections.
- Include a list of slides in correct order.
- For each slide, define:
    - slide_type (Title, Introduction, Problem, Solution, Approach, Benefits, Timeline, Team, Contact)
    - description (what the slide should communicate)
    - required_fields (what information must be asked from the user later)
- Do NOT generate slide content yet.
- Only define the structure and required info.
"""

def create_presentation_plan(user_prompt: str):
    """
    Converts user request → structured presentation plan.
    """

    USER_PROMPT = f"""
    User Request:
    {user_prompt}

    Create a JSON presentation plan with this structure:

    {{
        "goal": "Overall purpose of the deck",
        "slides": [
            {{
                "slide_type": "Title",
                "description": "Purpose of slide",
                "required_fields": ["project_name", "client_name", "presenter"]
            }},
            {{
                "slide_type": "Problem",
                "description": "Explain the problem statements",
                "required_fields": ["problems"]
            }}
        ]
    }}
    """

    result = chat_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        json_mode=True,
        temperature=0.1
    )

    if not isinstance(result, dict):
        logger.error("Planner returned unstructured data.")
        return {"goal": "", "slides": []}

    return result
