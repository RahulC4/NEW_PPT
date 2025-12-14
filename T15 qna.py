# pages/3_❓_QnA.py
import os
import streamlit as st
from utils import text_client, get_env, logger

st.set_page_config(page_title="3 - Q&A", layout="wide")
st.title("3 — Q&A (Slide-Specific Questions)")

# ------------------------------------------------------------------
# Load selected slides
# ------------------------------------------------------------------
slides = st.session_state.get("selected_slide_structs", [])
if not slides:
    st.error("No slides selected. Please go back to Slide Selection.")
    st.stop()

st.info(
    "The AI analyses each selected slide and asks 3–5 short, relevant questions. "
    "Answer them to generate a personalized presentation."
)

# ------------------------------------------------------------------
# LLM QUESTION GENERATION — numbered plain text (no JSON)
# ------------------------------------------------------------------
def generate_questions_for_slide(slide_struct):
    editable_shapes = slide_struct.get("editable_shapes", [])
    texts = [s["text"] for s in editable_shapes if s.get("text")]

    if not texts:
        raise ValueError("No text found to analyze in this slide.")

    prompt = f"""
You are analyzing the following PowerPoint slide content.

Slide Title: {slide_struct.get("title","")}
Slide Text:
{texts}

TASK:
Generate 3 to 5 short, specific, non-generic questions
to help the user refine or update this slide's content.

Rules:
- Questions must be based on this slide's actual content.
- Ask about items such as scope, goals, key points, or metrics.
- Do NOT ask generic things like "What is the title?".
- Return plain numbered text only, one question per line.

Example format:
1. What key metrics should be shown on this slide?
2. Which client segments should be included?
3. What are the major deliverables to highlight?
"""

    try:
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=500
        )
        raw = resp.choices[0].message.content.strip()
        if not raw:
            raise ValueError("LLM returned empty response.")

        # Parse numbered questions safely
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        questions = []
        for ln in lines:
            if ln[0].isdigit():
                # remove numbering like "1.", "1)", "1 -"
                q = ln.split(".", 1)[-1].strip() if "." in ln else ln
                q = q.split(")", 1)[-1].strip() if ")" in q else q
                if q:
                    questions.append(q)

        if not questions:
            raise ValueError(f"No valid questions parsed. Raw output:\n{raw}")

        return questions

    except Exception as e:
        logger.exception("LLM question generation failed")
        raise RuntimeError(f"Question generation failed: {e}")


# ------------------------------------------------------------------
# Generate questions once per slide
# ------------------------------------------------------------------
for slide in slides:
    qkey = f"plain_qna_{slide['slide_id']}"
    if qkey not in st.session_state:
        try:
            st.session_state[qkey] = generate_questions_for_slide(slide)
        except Exception as e:
            st.session_state[qkey] = [f"Error generating questions: {e}"]

# ------------------------------------------------------------------
# Display Q&A per slide
# ------------------------------------------------------------------
st.session_state.setdefault("answers_by_slide", {})

for idx, slide in enumerate(slides):
    slide_id = slide["slide_id"]
    qkey = f"plain_qna_{slide_id}"
    questions = st.session_state.get(qkey, [])

    st.markdown("---")
    st.subheader(f"Slide {idx+1}: {slide.get('title','Untitled Slide')}")

    if slide.get("png_path") and os.path.exists(slide["png_path"]):
        st.image(slide["png_path"], use_container_width=True)

    st.session_state["answers_by_slide"].setdefault(slide_id, {})

    for i, q in enumerate(questions):
        answer_key = f"{slide_id}_q{i}"
        val = st.text_area(
            label=q,
            value=st.session_state["answers_by_slide"][slide_id].get(q, ""),
            key=answer_key
        )
        st.session_state["answers_by_slide"][slide_id][q] = val

# ------------------------------------------------------------------
# Navigation
# ------------------------------------------------------------------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Slide Selection"):
        st.switch_page("pages/2_🖼️_Slide_Selection.py")

with col2:
    if st.button("➡ Generate PPT"):
        answers_for_generator = {}
        for slide in slides:
            idx = str(slide["slide_index"])
            answers_for_generator[idx] = st.session_state["answers_by_slide"].get(
                slide["slide_id"], {}
            )

        st.session_state["generation_payload"] = {
            "selected_slides": slides,
            "answers_map": answers_for_generator
        }
        st.switch_page("pages/4_Generate_PPT.py")
