def get_slide_title_from_chroma(slide):
    ppt_name = slide.get("ppt_blob")
    slide_index = slide.get("slide_index")

    if ppt_name is None or slide_index is None:
        return None

    try:
        res = collection.get(
            where={
                "$and": [
                    {"ppt_name": ppt_name},
                    {"slide_index": slide_index}
                ]
            }
        )

        metas = res.get("metadatas", [])
        if not metas:
            return None

        title = metas[0].get("title", "").strip()

        # 🚨 VALIDATION — reject bad titles
        if not title:
            return None

        if len(title) > 120:              # too long = body text
            return None

        if "\n" in title:                 # multiline = body text
            return None

        return title

    except Exception:
        logger.exception("Failed to fetch slide title from Chroma")
        return None
