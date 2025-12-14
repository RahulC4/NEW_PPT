# llm/slide_classifier.py

from llm.llm_utils import chat_completion
from utils import logger

SYSTEM_PROMPT = """
You are an expert in corporate presentations. 
Your task is to classify a slide into a standard slide type based on its text content.

Allowed slide types:
- Title
- Introduction
- Problem
- Solution
- Approach
- Benefits
- Timeline
- Team
- Contact
- Other

Rules:
- Read the slide text carefully.
- Select the BEST matching slide_type.
- Return ONLY valid JSON.

Example Output:
{
  "slide_type": "Problem",
  "confidence": 0.92
}
"""

def classify_slide(text: str):
    """
    Classify a slide based on textual content.
    Called during ingestion_chroma.py.
    """

    if not text or text.strip() == "":
        return {"slide_type": "Other", "confidence": 0.0}

    USER_PROMPT = f"""
    Slide Text:
    {text}

    Classify into slide_type and return JSON.
    """

    try:
        result = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT,
            json_mode=True,
            temperature=0.0
        )

        if not isinstance(result, dict):
            return {"slide_type": "Other", "confidence": 0.0}

        return {
            "slide_type": result.get("slide_type", "Other"),
            "confidence": result.get("confidence", 0.0)
        }

    except Exception as e:
        logger.warning(f"Slide classification failed: {e}")
        return {"slide_type": "Other", "confidence": 0.0}
