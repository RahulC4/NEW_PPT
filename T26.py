def get_exact_slide_text(slide, max_chars=1200):
    """
    Fetch exact slide text using ppt_blob + slide_index
    (NO embeddings, NO semantic search)
    """

    ppt_name = slide.get("ppt_blob")
    slide_index = slide.get("slide_index")

    if ppt_name is None or slide_index is None:
        logger.warning("[QNA] Missing ppt_blob or slide_index")
        return ""

    try:
        logger.info(
            f"[QNA] Fetching slide from Chroma | ppt={ppt_name} | index={slide_index}"
        )

        res = collection.get(
            where={
                "$and": [
                    {"ppt_name": ppt_name},
                    {"slide_index": slide_index}
                ]
            }
        )

        docs = res.get("documents", [])
        logger.info(f"[QNA] Retrieved {len(docs)} docs from Chroma")

        if not docs:
            return ""

        return "\n".join(docs)[:max_chars]

    except Exception:
        logger.exception("[QNA] Chroma get() failed")
        return ""







for idx, slide in enumerate(slides):
    slide_id = slide["slide_id"]

    # ✅ Prefer actual PPT title extracted from slide
    slide_title = (
        (slide.get("title") or "").strip()
        or f"Slide {idx + 1}"
    )

    questions = st.session_state["questions_by_slide"].get(slide_id, [])

    st.markdown("---")
    st.subheader(f"Slide {idx + 1}: {slide_title}")
