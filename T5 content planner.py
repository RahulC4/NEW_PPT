import json
from llm.llm_utils import chat_completion
from utils import logger

SYSTEM_PROMPT = """
You are generating content for a PowerPoint presentation.

For EACH slide, return a JSON object with:
- title: short slide title
- bullets: array of concise bullet points (3 to 6 bullets)

Rules:
- Do NOT repeat template/sample text verbatim
- Bullets must expand the slide title meaningfully
- Keep bullets short and professional
- No markdown, no explanations, only valid JSON
"""

def generate_slide_plan(user_prompt: str, slide_titles: list[str]) -> list[dict]:
    """
    Generates structured content for each slide.
    """

    slides = []

    for title in slide_titles:
        prompt = f"""
Slide title: {title}

User request:
{user_prompt}

Generate slide content.
"""

        response = chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.7
        )

        try:
            slide_content = json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse LLM output for slide '{title}': {e}")
            slide_content = {
                "title": title,
                "bullets": []
            }

        # Safety fallback
        slide_content.setdefault("title", title)
        slide_content.setdefault("bullets", [])

        slides.append(slide_content)

    logger.info(f"Generated content for {len(slides)} slides")
    return slides
