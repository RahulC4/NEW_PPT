# main_generator.py

import os
import tempfile
from utils import logger, now_ts
from llm.content_planner import create_presentation_plan
from llm.qna_engine import generate_questions, build_content_profile
from search.template_mapper import map_plan_to_templates
from ppt.ppt_builder import build_presentation
from storage.azure_blob_utils import upload_ppt_to_blob


# ================================================================
# HIGH-LEVEL ORCHESTRATION PIPELINE
# ================================================================
class PresentationGenerator:

    def __init__(self):
        pass

    # ------------------------------------------------------------
    # STEP 1 — PLAN PRESENTATION
    # ------------------------------------------------------------
    def plan_from_prompt(self, user_prompt: str):
        logger.info("Generating presentation plan...")
        plan = create_presentation_plan(user_prompt)
        return plan

    # ------------------------------------------------------------
    # STEP 2 — GENERATE QUESTIONS FROM PLAN
    # ------------------------------------------------------------
    def get_questions(self, plan: dict):
        logger.info("Generating Q&A questions...")
        questions = generate_questions(plan)
        return questions

    # ------------------------------------------------------------
    # STEP 3 — BUILD CONTENT PROFILE FROM USER ANSWERS
    # ------------------------------------------------------------
    def build_profile(self, plan: dict, user_answers: dict):
        logger.info("Building content profile...")
        profile = build_content_profile(plan, user_answers)
        return profile

    # ------------------------------------------------------------
    # STEP 4 — MAP PLAN TO TEMPLATE SLIDES
    # ------------------------------------------------------------
    def map_templates(self, plan: dict):
        logger.info("Mapping plan to slide templates...")
        mapped = map_plan_to_templates(plan)
        return mapped

    # ------------------------------------------------------------
    # STEP 5 — BUILD THE FINAL PPT
    # ------------------------------------------------------------
    def generate_ppt(self, mapped_templates, content_profile):
        logger.info("Generating PowerPoint...")

        tmp_output = os.path.join(
            tempfile.gettempdir(),
            f"generated_{now_ts().replace(':','_')}.pptx"
        )

        build_presentation(mapped_templates, content_profile, tmp_output)
        return tmp_output

    # ------------------------------------------------------------
    # STEP 6 — UPLOAD TO AZURE BLOB
    # ------------------------------------------------------------
    def upload_output(self, file_path: str):
        file_name = os.path.basename(file_path)
        blob_key = upload_ppt_to_blob(file_path, file_name)
        return blob_key


# ================================================================
# PUBLIC API (used by Streamlit or API)
# ================================================================
def create_presentation_pipeline(user_prompt: str, user_answers: dict):
    """
    A single convenience function to run the full pipeline end-to-end.
    Called by the UI layer.
    """

    engine = PresentationGenerator()

    # Step 1: Plan slides
    plan = engine.plan_from_prompt(user_prompt)

    # Step 2: Map templates
    mapped_templates = engine.map_templates(plan)

    # Step 3: Build content profile
    profile = engine.build_profile(plan, user_answers)

    # Step 4: Generate PPT
    output_path = engine.generate_ppt(mapped_templates, profile)

    # Step 5: Upload to Azure
    blob_path = engine.upload_output(output_path)

    return {
        "plan": plan,
        "mapped_templates": mapped_templates,
        "content_profile": profile,
        "ppt_blob_path": blob_path
    }
