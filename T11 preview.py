# pages/4_Preview_Slides.py
import streamlit as st
from generate_ppt_llm import llm_synthesize_slide

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

payload = st.session_state.get("generation_payload")

if not payload:
    st.error("No payload found. Complete Q&A first.")
    st.stop()

slides = payload["slides"]
answers_map = payload["answers_map"]

st.session_state.setdefault("preview_slides", [])

# -------------------------------------------------
# Generate preview ONCE using LLM
# -------------------------------------------------
if not st.session_state["preview_slides"]:
    preview = []

    for slide in slides:
        idx = str(slide["slide_index"])
        user_answers = answers_map.get(idx, {})

        # Title slide
        if "What should be the title of this presentation?" in user_answers:
            title = user_answers["What should be the title of this presentation?"]
            preview.append({
                "title": title,
                "bullets": []
            })
            continue

        # Normal content slide
        if any(v.strip() for v in user_answers.values()):
            _, bullets = llm_synthesize_slide(
                user_answers,
                global_prompt="professional business presentation"
            )
        else:
            bullets = []

        preview.append({
            "title": slide["slide_title"],
            "bullets": bullets
        })

    st.session_state["preview_slides"] = preview

# -------------------------------------------------
# RENDER PREVIEW (EDITABLE)
# -------------------------------------------------
for i, slide in enumerate(st.session_state["preview_slides"], start=1):
    st.markdown("---")
    st.subheader(f"Slide {i}")

    slide["title"] = st.text_input(
        "Slide Title",
        value=slide["title"],
        key=f"title_{i}"
    )

    st.markdown("**Bullets**")

    updated_bullets = []
    for j, b in enumerate(slide["bullets"]):
        txt = st.text_input(
            "",
            value=b,
            key=f"b_{i}_{j}",
            label_visibility="collapsed"
        )
        if txt.strip():
            updated_bullets.append(txt)

    if st.button("➕ Add Bullet", key=f"add_{i}"):
        updated_bullets.append("")

    slide["bullets"] = updated_bullets

# -------------------------------------------------
# SAVE & NAVIGATE
# -------------------------------------------------
st.markdown("---")
if st.button("🎯 Generate PPT"):
    payload["slides"] = st.session_state["preview_slides"]
    st.session_state["generation_payload"] = payload
    st.switch_page("pages/5_Generate_PPT.py")
