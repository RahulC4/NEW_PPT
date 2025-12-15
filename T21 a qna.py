def get_exact_slide_text(slide, max_chars=1200):
    ppt_name = slide.get("ppt_blob")
    slide_id = slide.get("slide_id")

    if not ppt_name or not slide_id:
        return ""

    try:
        res = collection.get(
            where={
                "ppt_name": ppt_name,
                "slide_id": slide_id
            }
        )
    except Exception:
        logger.exception("Exact Chroma get() failed")
        return ""

    docs = res.get("documents", [])
    if not docs:
        return ""

    text = "\n".join(docs)
    return text[:max_chars]
