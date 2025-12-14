# pages/3_❓_QnA.py

import os
import json
import streamlit as st
from utils import text_client, get_env, safe_json_load, logger

st.set_page_config(page_title="3 - QnA", layout="wide")
st.title("3 — Q&A (Slide-specific questions)")

# -------------------------------------------------------------------
# Load selected slide STRUCTURES (not IDs)
# -------------------------------------------------------------------
slides = st.session_state.get("selected_slide_structs", [])

if not slides:
    st.error("No selected slides found. Please go back to Slide Selection.")
    st.stop()

# Hard validation to prevent string/dict mismatch bugs
if not isinstance(slides, list) or not isinstance(slides[0], dict):
    st.error("Invalid slide data passed to QnA page. Expected slide structures.")
    st.stop()

st.info(
    "Answer the questions generated for each slide. "
    "These questions are derived from the actual slide content."
)

# -------------------------------------------------------------------
# LLM: Generate slide-aware questions
# -------------------------------------------------------------------
def generate_questions_for_slide(slide: dict) -> dict:
    """
    Returns:
        {
          "title": "...",
          "questions": [
             {"key": "...", "question": "..."},
             ...
          ]
        }
    """

    slide_title = slide.get("title", "")
    slide_text_blocks = [s["text"] for s in slide.get("editable_shapes", []) if s.get("text")]

    prompt = f"""
You are analysing a PowerPoint slide and must generate intelligent,
context-aware questions to collect user input for regenerating the slide.

Slide title:
{slide_title}

Slide text content:
{json.dumps(slide_text_blocks, indent=2)}

Rules:
- Questions MUST be derived from the slide content
- Ask about items such as scope, LOBs, key points, metrics, assumptions, customisations
- Do NOT ask generic questions
- Generate 2–5 questions depending on content richness
- Return JSON ONLY in the following format:

{{
  "title": "<rewritten concise slide title>",
  "questions": [
    {{
      "key": "lob_list",
      "question": "Which lines of business should be included?"
    }}
  ]
}}
"""

    try:
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=[
                {"role": "system", "content": "You are a PPT slide analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,   # important for deterministic questions
            max_completion_tokens=800,
        )

        raw = resp.choices[0].message.content.strip()
        parsed = safe_json_load(raw)

        if not isinstance(parsed, dict) or "questions" not in parsed:
            raise ValueError("Invalid LLM response format")

        return parsed

    except Exception as e:
        logger.exception("Failed to generate slide questions")
        st.error(f"LLM question generation failed: {e}")
        st.stop()


# -------------------------------------------------------------------
# Generate questions ONCE per slide
# -------------------------------------------------------------------
for slide in slides:
    qkey = f"qna_{slide['slide_id']}"
    if qkey not in st.session_state:
        st.session_state[qkey] = generate_questions_for_slide(slide)

# Storage for answers
st.session_state.setdefault("answers_by_slide", {})

# -------------------------------------------------------------------
# UI Rendering
# -------------------------------------------------------------------
for slide in slides:
    slide_id = slide["slide_id"]
    slide_index = slide["slide_index"]
    qna = st.session_state[f"qna_{slide_id}"]

    st.markdown(
        f"## Slide {slide_index + 1}: {qna.get('title') or slide.get('title','')}"
    )

    # Show slide thumbnail
    if slide.get("png_path") and os.path.exists(slide["png_path"]):
        st.image(slide["png_path"], use_container_width=True)

    st.session_state["answers_by_slide"].setdefault(slide_id, {})

    for q in qna["questions"]:
        key = q["key"]
        label = q["question"]

        st.session_state["answers_by_slide"][slide_id][key] = st.text_area(
            label,
            value=st.session_state["answers_by_slide"][slide_id].get(key, ""),
            key=f"{slide_id}_{key}",
        )

    st.divider()

# -------------------------------------------------------------------
# Navigation
# -------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Slide Selection"):
        st.switch_page("pages/2_🖼️_Slide_Selection.py")

with col2:
    if st.button("Generate PPT"):
        st.session_state["generation_payload"] = {
            "selected_slides": slides,   # FULL STRUCTS
            "answers_map": st.session_state["answers_by_slide"],
        }
        st.switch_page("pages/4_Generate_PPT.py")
