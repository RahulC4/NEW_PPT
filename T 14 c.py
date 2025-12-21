from generate_ppt_llm import llm_synthesize_slide

# ---------------------------------------------------
# INIT PREVIEW STATE (ALWAYS LLM-SYNTHESIZED)
# ---------------------------------------------------
if not st.session_state["preview_slides"]:
    preview = []

    for s in slides:
        slide_idx = str(s["slide_index"])
        user_answers = answers_map.get(slide_idx, {})

        try:
            # ✅ ALWAYS synthesize via LLM
            llm_title, llm_bullets = llm_synthesize_slide(
                user_answers=user_answers,
                global_prompt="professional business presentation"
            )
        except Exception:
            llm_title = s["slide_title"]
            llm_bullets = ["Content could not be generated"]

        preview.append({
            "slide_index": s["slide_index"],
            # 🔒 Title preference: LLM → slide title
            "title": llm_title or s["slide_title"],
            "bullets": llm_bullets[:6] or ["Click to edit bullet"]
        })

    st.session_state["preview_slides"] = preview
