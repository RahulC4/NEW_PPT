import streamlit as st
import json

from utils import logger, text_client
from slide_renderer import render_slide_thumbnail


# -------------------------------
# Session State Guards
# -------------------------------
if "selected_slides" not in st.session_state:
    st.warning("No slides selected. Please go back to Slide Selection.")
    st.stop()

if "answers_map" not in st.session_state:
    st.session_state.answers_map = {}

slides = st.session_state.selected_slides

st.title("3 – QnA")
st.caption("Answer a few questions per slide. These answers will be used to generate the final PPT.")


# -------------------------------
# LLM QUESTION GENERATION
# -------------------------------
def generate_questions_for_slide(slide):
    slide_text = (
        slide.get("text")
        or slide.get("all_text")
        or slide.get("raw_text")
        or ""
    )

    if not slide_text.strip():
        raise ValueError("Slide text is empty — cannot generate intelligent questions")

    prompt = f"""
You are analyzing a PowerPoint slide.

SLIDE TITLE:
{slide.get("title", "")}

SLIDE CONTENT:
{slide_text}

TASK:
Generate 3–5 highly specific clarification questions that will help rewrite or enhance
this slide content. Questions must be tightly grounded in the slide content.

RULES:
- Do NOT ask generic questions
- Do NOT ask about presentation length
- Questions must be directly related to this slide
- Return STRICT JSON only

FORMAT:
{{
  "questions": [
    "question 1",
    "question 2",
    "question 3"
  ]
}}
"""

    response = text_client.chat.completions.create(
        model=st.session_state.get("CHAT_MODEL"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed.get("questions"), list) and len(parsed["questions"]) >= 2:
            return parsed["questions"]
        raise ValueError("Invalid question format")
    except Exception:
        logger.exception("Failed to parse LLM questions")
        raise


# -------------------------------
# UI LOOP PER SLIDE
# -------------------------------
for idx, slide in enumerate(slides):
    slide_id = slide["slide_id"]

    st.markdown("---")
    cols = st.columns([1, 3])

    # Left: slide image
    with cols[0]:
        render_slide_thumbnail(slide)

    # Right: title + questions
    with cols[1]:
        st.subheader(slide.get("title", f"Slide {idx + 1}"))

        # Generate questions once
        if slide_id not in st.session_state.answers_map:
            try:
                questions = generate_questions_for_slide(slide)
                st.session_state.answers_map[slide_id] = {
                    "questions": questions,
                    "answers": [""] * len(questions),
                }
            except Exception as e:
                st.error(f"Failed to generate questions: {e}")
                continue

        qna = st.session_state.answers_map[slide_id]

        for q_idx, question in enumerate(qna["questions"]):
            qna["answers"][q_idx] = st.text_area(
                label=question,
                value=qna["answers"][q_idx],
                key=f"{slide_id}_{q_idx}",
            )


# -------------------------------
# NAVIGATION
# -------------------------------
st.markdown("---")

if st.button("➡️ Generate PPT"):
    # Build payload expected by generate_presentation()
    st.session_state.generation_payload = {
        "selected_slides": slides,
        "answers_map": {
            slide_id: {
                "questions": data["questions"],
                "answers": data["answers"],
            }
            for slide_id, data in st.session_state.answers_map.items()
        },
    }

    st.switch_page("pages/4_Generate_PPT.py")
