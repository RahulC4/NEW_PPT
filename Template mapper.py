# search/template_mapper.py

from search.search_utils import semantic_search
from utils import logger

"""
TemplateMapper maps each slide_type (Title, Problem, Solution, etc.)
to the best matching slide template from the ingested PPT dataset.

The ingestion stores:
- text content
- slide_type (from classifier)
- layout_id
- master_id
- placeholder structures (to be added in updated ingestion)
"""

def get_best_template(slide_type: str, top_k: int = 5):
    """
    Retrieve the best template slide for a given slide_type.
    Uses semantic search with the slide_type as query.
    """

    query = f"Corporate PowerPoint slide for {slide_type} section"

    # Filter by metadata in future ingestion update
    results = semantic_search(query=query, top_k=top_k)

    if not results:
        logger.warning(f"No templates found for slide_type: {slide_type}")
        return None

    # BEST candidate is result[0]
    best = results[0]

    logger.info(f"Selected template for {slide_type}: {best['slide_id']} ({best['ppt_name']})")

    return {
        "ppt_name": best["ppt_name"],
        "slide_id": best["slide_id"],
        "slide_type": slide_type,
        "title": best.get("title", ""),
        "text": best.get("text", ""),
        "tags": best.get("tags", ""),
        # Layout metadata added later in updated ingestion
        "layout": best.get("layout", None),
        "placeholders": best.get("placeholders", None)
    }


def map_plan_to_templates(plan: dict):
    """
    Given the slide plan from content_planner,
    return template slide metadata for each required slide.
    """

    mapped = []

    for slide in plan.get("slides", []):
        slide_type = slide.get("slide_type")
        template = get_best_template(slide_type)

        if template is None:
            logger.warning(f"Could not find template for slide type: {slide_type}")
            template = {"slide_type": slide_type, "template_missing": True}

        mapped.append({
            "requested_slide": slide,
            "template": template
        })

    return mapped
