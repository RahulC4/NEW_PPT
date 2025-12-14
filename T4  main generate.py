import os
import uuid
from utils import logger
from llm.content_planner import generate_slide_plan
from search.template_mapper import map_plan_to_templates
from ppt.ppt_builder import build_presentation


def generate_ppt(user_prompt: str, user_answers: dict) -> str:
    logger.info("Starting PPT generation")

    # 1. Generate slide plan
    slide_plan = generate_slide_plan(user_prompt)

    # 2. Map plan to stored PPT templates
    mapped_templates = map_plan_to_templates(slide_plan)

    # 3. Ensure output directory exists
    output_dir = "generated"
    os.makedirs(output_dir, exist_ok=True)

    # 4. Build PPT
    output_name = f"generated_{uuid.uuid4().hex[:8]}.pptx"
    output_path = os.path.join(output_dir, output_name)

    build_presentation(
        mapped_templates=mapped_templates,
        content_profile=user_answers,
        output_path=output_path,
    )

    logger.info(f"PPT generated at {output_path}")
    return output_path
