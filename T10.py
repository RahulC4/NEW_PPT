# ============================================================
# 🔍 PREVIEW
# ============================================================
col_p1, col_p2, _ = st.columns([2, 2, 4])

with col_p1:
    preview_clicked = st.button("🔍 Preview Slide Plan")

with col_p2:
    generated_clicked = st.button("🎯 Generate PPT")

if preview_clicked:
    if not prompt.strip():
        st.error("Please enter a prompt.")
    else:
        with st.spinner("Searching knowledge base & generating preview..."):
            try:
                raw_refs = semantic_search(prompt, top_k=5)
                refs = [
                    r for r in (raw_refs or [])
                    if r.get("score") is None or r["score"] <= SIMILARITY_THRESHOLD
                ]

                if not refs:
                    st.warning(
                        "⚠️ I couldn’t find any relevant content in your uploaded PPTs "
                        "for this prompt. Please rephrase using topics related to your "
                        "sample decks or upload a new PPT."
                    )
                else:
                    ref_text = [
                        (r.get("text") or "")[:400]
                        for r in refs
                        if r.get("text")
                    ]

                    plan = call_llm_plan(
                        prompt=prompt,
                        references_text=ref_text,
                        num_slides=num_slides,
                    )

                    if not plan:
                        st.warning(
			    "⚠️ Not enough relevant content to generate this many slides. "
                            "Try reducing slide count or rephrasing.")
                    else:
                        st.subheader("📝 Slide Plan Preview")
                        for i, slide in enumerate(plan, start=1):
                            st.markdown(f"### Slide {i}: {slide.get('title','Untitled')}")
                            bullets = slide.get("bullets", [])
                            if bullets:
                                st.markdown("\n".join(f"- {b}" for b in bullets))
            except Exception as e:
                logger.exception("Preview failed")
                st.error(f"Error while generating preview: {e}")

st.markdown("---")
