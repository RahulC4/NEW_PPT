def get_exact_slide_text(slide, max_chars=1200):
    """
    Fetch exact slide text from Chroma using slide_index (NOT slide_id)
    """
    slide_index = slide.get("slide_index")

    if slide_index is None:
        return ""

    try:
        res = collection.get(
            where={
                "slide_index": slide_index
            },
            include=["documents"]
        )
    except Exception:
        logger.exception("Exact Chroma get() by slide_index failed")
        return ""

    docs = res.get("documents", [])
    if not docs:
        logger.error(f"No Chroma documents for slide_index={slide_index}")
        return ""

    text = "\n".join(docs)
    return text[:max_chars]
