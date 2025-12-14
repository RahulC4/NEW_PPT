import os
import uuid

from llm.content_planner import generate_slide_plan
from search.template_mapper import map_plan_to_templates
from ppt.ppt_builder import build_presentation
from utils import logger


def generate_ppt(user_prompt: str):
    """
    End-to-end PPT generation pipeline
    """

    logger.info("Starting PPT generation pipeline")

    # -------------------------------------------------
    # 1️⃣ DEFINE SLIDE TITLES (FROM TEMPLATE STRUCTURE)
    # -------------------------------------------------
    # These come from your indexed dataset / templates
    slide_titles = [
        "Introduction",
        "Business Overview",
        "Problem Statement",
        "Proposed Solution",
        "Benefits",
        "Conclusion"
    ]

    # -------------------------------------------------
    # 2️⃣ GENERATE CONTENT USING LLM
    # -------------------------------------------------
    slide_plan = generate_slide_plan(
        user_prompt=user_prompt,
        slide_titles=slide_titles
    )

    # -------------------------------------------------
    # 3️⃣ MAP CONTENT TO PPT TEMPLATES
    # -------------------------------------------------
    mapped_templates = map_plan_to_templates(slide_plan)

    # -------------------------------------------------
    # 4️⃣ BUILD PPT
    # -------------------------------------------------
    output_name = f"generated_{uuid.uuid4().hex[:8]}.pptx"
    output_path = os.path.join("generated", output_name)

    os.makedirs("generated", exist_ok=True)

    build_presentation(
        mapped_templates=mapped_templates,
        content_profile=slide_plan,
        output_path=output_path
    )

    logger.info(f"PPT generation completed: {output_path}")
    return output_path
