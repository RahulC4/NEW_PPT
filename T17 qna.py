# pages/3_❓_QnA.py

import streamlit as st
from utils import text_client, logger

st.set_page_config(page_title="QnA", layout="wide")

st.title("3 — Q&A (Slide-specific questions)")
st.caption("Answer a few questions per slide. These answers will be used to generate slide content.")

# ---------------------------------------------------------
# 1. Read selected slides safely
# ---------------------------------------------------------
selected_slides = st.session_state.get("selected_slides")

if not selected_slides:
    st.error("No slide selection found. Please select slides first.")
    st.stop()

# Initialise answer store
if "answers_by_slide" not in st.session_state:
    st.session_state["answers_by_slide"] = {}

# ---------------------------------------------------------
# 2. Helper: generate questions (PLAIN TEXT, NO JSON)
# ---------------------------------------------------------
def generate_questions_for_slide(slide):
    """
    Returns a list of questions (strings) derived from slide content.
    Uses plain text to avoid JSON failures.
    """

    slide_title = slide.get("title", "Untitled slide")
    slide_text = slide.get("text", "")

    prompt = f"""
You are analysing a PowerPoint slide to collect inputs from a user.

Slide title:
{slide_title}

Slide content:
{slide_text}

Generate 3 to 5 clear, practical questions that:
- Help gather information to create this slide
- Are specific to this slide's topic
- Ask for bullet-friendly content
- Avoid yes/no questions

Return ONLY the questions, one per line.
Do NOT number them.
Do NOT return JSON.
"""

    try:
        resp = text_client.chat.completions.create(
            model=st.session_state.get("chat_model"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        raw = resp.choices[0].message.content.strip()
        questions = [q.strip("-• ").strip() for q in raw.split("\n") if q.strip()]
        return questions[:5]
    except Exception as e:
        logger.exception("LLM question generation failed")
        raise RuntimeError(f"LLM question generation failed: {e}")

# ---------------------------------------------------------
# 3. UI per slide
# ---------------------------------------------------------
for slide in selected_slides:
    slide_id = slide["slide_id"]
    title = slide.get("title", f"Slide {slide_id}")
    preview = slide.get("preview_image")

    st.divider()
    st.subheader(title)

    if preview:
        st.image(preview, width=260)

    # Generate questions once
    if slide_id not in st.session_state["answers_by_slide"]:
        with st.spinner("Generating questions..."):
            questions = generate_questions_for_slide(slide)

        st.session_state["answers_by_slide"][slide_id] = {
            "questions": questions,
            "answers": {}
        }

    qdata = st.session_state["answers_by_slide"][slide_id]

    # Render questions
    for idx, q in enumerate(qdata["questions"], start=1):
        key = f"{slide_id}_q_{idx}"
        answer = st.text_area(
            label=q,
            value=qdata["answers"].get(q, ""),
            key=key,
            height=80
        )
        qdata["answers"][q] = answer

# ---------------------------------------------------------
# 4. Continue button
# ---------------------------------------------------------
st.divider()

if st.button("Continue to Generate PPT"):
    st.session_state["qna_completed"] = True
    st.switch_page("pages/4_Generate_PPT.py")
