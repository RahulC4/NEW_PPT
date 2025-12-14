from search.search_utils import semantic_search
from utils import logger


def map_plan_to_templates(plan, top_k=1):
    """
    Maps each slide section to a template slide layout.
    """

    mapped = []

    for section in plan["slides"]:
        query = section["title"]

        results = semantic_search(query, top_k=top_k)
        if not results:
            logger.warning(f"No template found for {query}")
            continue

        best = results[0]

        mapped.append({
            "section": section["key"],
            "layout_name": best["metadata"]["layout_name"],
            "master_name": best["metadata"]["master_name"],
            "placeholders": best["metadata"]["placeholders"],
        })

    return mapped
