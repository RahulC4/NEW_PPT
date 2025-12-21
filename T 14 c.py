from generate_ppt_llm import llm_synthesize_slide

# ---------------------------------------------------
# INIT PREVIEW STATE (LLM GENERATED CONTENT – ONCE PER SELECTION)
# ---------------------------------------------------
st.session_state.setdefault("preview_slides", [])

# 🔑 Reset preview if slide selection changed
current_slide_ids = [str(s["slide_index"]) for s in slides]
prev_ids = st.session_state.get("_preview_slide_ids")

if prev_ids != current_slide_ids:
    st.session_state["preview_slides"] = []
    st.session_state["_preview_slide_ids"] = current_slide_ids


if not st.session_state["preview_slides"]:
    preview = []

    for s in slides:
        slide_idx = str(s["slide_index"])
        user_answers = answers_map.get(slide_idx, {})

        # ✅ ALWAYS GENERATE FROM LLM (never raw Q&A)
        try:
            llm_title, llm_bullets = llm_synthesize_slide(
                user_answers=user_answers,
                global_prompt="professional business presentation"
            )
        except Exception:
            llm_title = s["slide_title"]
            llm_bullets = ["Content could not be generated"]

        preview.append({
            "slide_index": s["slide_index"],
            "title": llm_title or s["slide_title"],
            "bullets": llm_bullets[:6] or ["Click to edit bullet"]
        })

    st.session_state["preview_slides"] = preview
