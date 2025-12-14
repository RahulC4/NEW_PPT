from llm.llm_utils import chat_completion
from utils import logger

SYSTEM_PROMPT = """
You are a presentation planning assistant.

Create a structured slide plan for a professional presentation.
Return JSON only.
"""

USER_TEMPLATE = """
User request:
{prompt}

Create slides with the following structure:
- title
- introduction
- problem
- solution
- team
- contact

Each slide must have:
- key
- title
"""


def generate_slide_plan(user_prompt: str):
    """
    Generate a slide plan using LLM.
    """

    prompt = USER_TEMPLATE.format(prompt=user_prompt)

    logger.info("Generating slide plan using LLM")

    response = chat_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        temperature=0.3,
    )

    try:
        import json
        plan = json.loads(response)
        return plan
    except Exception:
        logger.error("Failed to parse slide plan JSON")
        raise ValueError("LLM did not return valid JSON")
