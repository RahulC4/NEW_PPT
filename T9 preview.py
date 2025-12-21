# pages/4_🖼️_Preview.py
import streamlit as st
from utils import text_client, get_env
from generate_ppt_llm import llm_synthesize_slide

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

payload = st.session_state.get("generation_payload")
if not payload:
    st.error("No payload found. Go back to Q&A.")
    st.stop()

slides = payload["slides"]
answers_map = payload["answers_map"]

# ----------------------------------------
# Generate preview ONCE using LLM
# ----------------------------------------
if "preview_slides" not in st.session_state:
    preview = []

    for s in slides:
        idx = str(s["slide_index"])
        user_answers = answers_map.get(idx, {})

        title, bullets = llm_synthesize_slide(
            user_answers=user_answers,
            global_prompt="professional business presentation"
        )

        preview.append({
            "slide_index": s["slide_index"],
            "title": title,
            "bullets": bullets
        })

    st.session_state["preview_slides"] = preview

# ----------------------------------------
# Editable Preview Canvas
# ----------------------------------------
for i, slide in enumerate(st.session_state["preview_slides"]):
    st.markdown("---")
    st.subheader(f"Slide {i+1}")

    # ✏️ Editable title
    slide["title"] = st.text_input(
        "Title",
        value=slide["title"],
        key=f"title_{i}"
    )

    # ✏️ Editable bullets (ENTER = new bullet)
    bullets_text = "\n".join(slide["bullets"])
    edited = st.text_area(
        "Bullets (Enter = new bullet)",
        value=bullets_text,
        height=150,
        key=f"bullets_{i}"
    )

    slide["bullets"] = [
        b.strip() for b in edited.split("\n") if b.strip()
    ]

# ----------------------------------------
# Navigation
# ----------------------------------------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Q&A"):
        st.switch_page("pages/3_❓_QnA.py")

with col2:
    if st.button("➡ Generate Final PPT"):
        payload["preview_slides"] = st.session_state["preview_slides"]
        st.session_state["generation_payload"] = payload
        st.switch_page("pages/5_Generate_PPT.py")
