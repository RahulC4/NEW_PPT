def get_exact_slide_text(slide, max_chars=1200):
    """
    Fetch ALL chunks belonging to the selected slide
    and merge them into a single context.
    """
    slide_index = slide.get("slide_index")
    if slide_index is None:
        return ""

    try:
        res = collection.query(
            where={"slide_index": slide_index},
            n_results=20  # enough to fetch all chunks of one slide
        )
    except Exception:
        logger.exception("Chroma query failed for exact slide retrieval")
        return ""

    documents = res.get("documents", [])
    if not documents:
        return ""

    # documents = List[List[str]] → flatten safely
    flat_docs = []
    for group in documents:
        if isinstance(group, list):
            flat_docs.extend(group)

    text = "\n".join(flat_docs).strip()
    return text[:max_chars]
