def get_exact_slide_text(slide, max_chars=1200):
    """
    Fetch exact slide text from Chroma using slide_id + slide_index
    """
    slide_id = slide.get("slide_id")
    slide_index = str(slide.get("slide_index"))

    if not slide_id:
        return ""

    try:
        res = collection.get(
            where={
                "slide_id": slide_id,
                "slide_index": slide_index
            }
        )
    except Exception:
        logger.exception("Exact Chroma get() failed")
        return ""

    docs = res.get("documents", [])
    if not docs:
        return ""

    return "\n".join(docs)[:max_chars]


context = get_exact_slide_text(slide)
if not context:
    return []
