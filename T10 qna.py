# pages/3_❓_QnA.py

import json
import streamlit as st
from utils import text_client, logger, safe_json_load, get_env

st.set_page_config(page_title="3 - QnA", layout="wide")
st.title("3 — Q&A (Slide-aware questions)")

# ------------------------------------------------------------------
# Load selected slides
# ------------------------------------------------------------------
selected_slides = st.session_state.get("selected_slide_structs", [])

if not selected_slides:
    st.warning("No slides selected. Go back to Slide Selection.")
    st.stop()

st.info("Answer slide-specific questions. Your answers will be used to generate slide content.")

# ------------------------------------------------------------------
# LLM QUESTION GENERATION (SLIDE-LEVEL)
# ------------------------------------------------------------------
def generate_slide_questions(slide):
    slide_text = slide.get("text", "")[:1500]
    slide_title = slide.get("title", "")

    system_prompt = """
You are an enterprise presentation expert.

Your task:
- Analyze the slide content and infer its intent
- Generate 3 to 5 highly relevant questions
- Questions must help generate slide bullet content
- Questions must be client/proposal focused
- Return ONLY valid JSON

JSON schema:
{
  "slide_intent": "<short intent>",
  "questions": [
    "<question 1>",
    "<question 2>",
    "<question 3>"
  ]
}
"""

    user_prompt = f"""
Slide title:
{slide_title}

Slide content:
{slide_text}
"""

    try:
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=600
        )

        raw = resp.choices[0].message.content.strip()
        logger.info(f"QnA RAW RESPONSE:\n{raw}")

        parsed = safe_json_load(raw)

        if isinstance(parsed, dict) and isinstance(parsed.get("questions"), list):
            return parsed

    except Exception as e:
        logger.exception("LLM question generation failed")

    # HARD fallback (rare now)
    return {
        "slide_intent": "General content",
        "questions": [
            "What key points should this slide cover?",
            "Any client-specific details to highlight?",
            "Any assumptions or constraints to mention?"
        ]
    }

# ------------------------------------------------------------------
# Initialize session state
# ------------------------------------------------------------------
st.session_state.setdefault("answers_by_slide", {})
st.session_state.setdefault("questions_by_slide", {})

# ------------------------------------------------------------------
# Render QnA UI
# ------------------------------------------------------------------
for slide in selected_slides:
    slide_id = slide["slide_id"]

    if slide_id not in st.session_state["questions_by_slide"]:
        st.session_state["questions_by_slide"][slide_id] = generate_slide_questions(slide)

    qdata = st.session_state["questions_by_slide"][slide_id]
    questions = qdata["questions"]

    st.markdown(f"### {slide.get('title', 'Slide')}")
    st.caption(f"Intent: {qdata.get('slide_intent')}")

    st.session_state["answers_by_slide"].setdefault(slide_id, [])

    for idx, q in enumerate(questions):
        key = f"ans_{slide_id}_{idx}"
        answer = st.text_area(q, key=key)
        if len(st.session_state["answers_by_slide"][slide_id]) <= idx:
            st.session_state["answers_by_slide"][slide_id].append(answer)
        else:
            st.session_state["answers_by_slide"][slide_id][idx] = answer

    st.markdown("---")

# ------------------------------------------------------------------
# Navigation
# ------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Generate PPT"):
        st.session_state["generation_payload"] = {
            "selected_slides": selected_slides,
            "answers_map": st.session_state["answers_by_slide"]
        }
        st.switch_page("pages/4_Generate_PPT.py")

with col2:
    if st.button("Back to Slide Selection"):
        st.switch_page("pages/2_🖼️_Slide_Selection.py")
