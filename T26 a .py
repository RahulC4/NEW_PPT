def get_slide_title_from_chroma(slide):
    ppt_name = slide.get("ppt_blob") or slide.get("ppt_name")
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
        if metas and metas[0].get("title"):
            return metas[0]["title"].strip()

    except Exception:
        logger.exception("Failed to fetch slide title from Chroma")

    return None


for idx, slide in enumerate(slides):
    slide_id = slide["slide_id"]

    slide_title = (
        get_slide_title_from_chroma(slide)
        or (slide.get("title") or "").strip()
        or f"Slide {idx + 1}"
    )

    questions = st.session_state["questions_by_slide"].get(slide_id, [])

    st.markdown("---")
    st.subheader(f"Slide {idx + 1}: {slide_title}")
