import os
import uuid

from llm.content_planner import generate_slide_plan
from search.template_mapper import map_plan_to_templates
from ppt.ppt_builder import build_presentation
from utils import logger


def generate_ppt(user_prompt: str, user_answers: dict):
    """
    Main orchestration function.
    """

    logger.info("Starting PPT generation pipeline")

    # -------------------------------------------------
    # 1. Generate slide plan from LLM
    # -------------------------------------------------
    plan = generate_slide_plan(user_prompt)
    logger.info("Slide plan generated")

    # -------------------------------------------------
    # 2. Map plan to stored slide templates
    # -------------------------------------------------
    mapped_templates = map_plan_to_templates(plan)
    logger.info("Templates mapped using semantic search")

    # -------------------------------------------------
    # 3. Build PPT
    # -------------------------------------------------
    output_name = f"generated_{uuid.uuid4().hex[:8]}.pptx"
    output_path = os.path.join("generated", output_name)

    build_presentation(
        mapped_templates=mapped_templates,
        content_profile=user_answers,
        output_path=output_path
    )

    logger.info("PPT generation completed")

    return output_path
