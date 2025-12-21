import streamlit as st
from generate_ppt_llm import llm_synthesize_slide
from utils import logger

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

payload = st.session_state.get("generation_payload")
if not payload:
    st.error("Missing generation payload")
    st.stop()

slides = payload["slides"]
answers_map = payload["answers_map"]

st.session_state.setdefault("preview_slides", [])

# ----------------------------------------------------
# Generate preview ONCE
# ----------------------------------------------------
if not st.session_state["preview_slides"]:
    preview = []
    for slide in slides:
        idx = str(slide["slide_index"])
        title = slide["slide_title"]
        answers = answers_map.get(idx, {})

        if "What should be the title of this presentation?" in answers:
            preview.append({
                "type": "title",
                "title": answers["What should be the title of this presentation?"],
                "bullets": []
            })
            continue

        valid = any(v.strip() for v in answers.values())
        if not valid:
            preview.append({
                "type": "content",
                "title": title,
                "bullets": []
            })
            continue

        try:
            _, bullets = llm_synthesize_slide(
                answers,
                "professional business presentation"
            )
        except Exception:
            logger.exception("Preview generation failed")
            bullets = []

        preview.append({
            "type": "content",
            "title": title,
            "bullets": bullets
        })

    st.session_state["preview_slides"] = preview

# ----------------------------------------------------
# UI — Editable Preview
# ----------------------------------------------------
for i, slide in enumerate(st.session_state["preview_slides"]):
    st.markdown("---")

    slide["title"] = st.text_input(
        f"Slide {i+1} Title",
        value=slide["title"],
        key=f"title_{i}"
    )

    new_bullets = []
    for j, b in enumerate(slide["bullets"]):
        val = st.text_input(
            f"Bullet {j+1}",
            value=b,
            key=f"bullet_{i}_{j}"
        )
        if val.strip():
            new_bullets.append(val)

    slide["bullets"] = new_bullets

# ----------------------------------------------------
# Navigation
# ----------------------------------------------------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Q&A"):
        st.switch_page("pages/3_❓_QnA.py")

with col2:
    if st.button("➡ Generate Final PPT"):
        st.session_state["final_slides"] = st.session_state["preview_slides"]
        st.switch_page("pages/5_🎯_Generate_PPT.py")
