# pages/4_Preview_Slides.py
import streamlit as st
from generate_ppt_llm import llm_synthesize_slide
from utils import logger

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

slides = st.session_state.get("generation_payload", {}).get("slides", [])
answers_map = st.session_state.get("generation_payload", {}).get("answers_map", {})

if not slides:
    st.error("No slides available for preview.")
    st.stop()

# -------------------------------------------------
# INIT preview storage (LLM runs ONLY once)
# -------------------------------------------------
st.session_state.setdefault("preview_slides", [])

if not st.session_state["preview_slides"]:
    preview = []

    for slide in slides:
        slide_idx = str(slide["slide_index"])
        user_answers = answers_map.get(slide_idx, {})

        # Title slide handled separately
        if "What should be the title of this presentation?" in user_answers:
            title = user_answers["What should be the title of this presentation?"]
            preview.append({
                "type": "title",
                "title": title,
                "bullets": []
            })
            continue

        try:
            llm_title, bullets = llm_synthesize_slide(
                user_answers,
                "professional business presentation"
            )
        except Exception:
            logger.exception("LLM failed during preview")
            llm_title = slide["slide_title"]
            bullets = ["Content could not be generated"]

        preview.append({
            "type": "content",
            "title": slide["slide_title"],
            "bullets": bullets
        })

    st.session_state["preview_slides"] = preview

# -------------------------------------------------
# RENDER EDITABLE PREVIEW
# -------------------------------------------------
for i, slide in enumerate(st.session_state["preview_slides"]):
    st.markdown("---")

    # Editable title
    slide["title"] = st.text_input(
        f"Slide {i+1} Title",
        value=slide["title"],
        key=f"title_{i}"
    )

    # Editable bullets
    bullets = slide.get("bullets", [])
    updated_bullets = []

    for j, b in enumerate(bullets):
        val = st.text_input(
            f"Bullet {j+1}",
            value=b,
            key=f"bullet_{i}_{j}"
        )
        if val.strip():
            updated_bullets.append(val)

    # ➕ Add new bullet
    new_bullet = st.text_input(
        "➕ Add new bullet",
        key=f"add_bullet_{i}"
    )
    if new_bullet.strip():
        updated_bullets.append(new_bullet)

    slide["bullets"] = updated_bullets

# -------------------------------------------------
# NAVIGATION
# -------------------------------------------------
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Q&A"):
        st.switch_page("pages/3_❓_QnA.py")

with col2:
    if st.button("✅ Generate PPT"):
        st.switch_page("pages/5_Generate_PPT.py")
