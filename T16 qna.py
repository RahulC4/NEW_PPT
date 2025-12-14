import streamlit as st
from utils import logger, text_client
from slide_renderer import render_slide_thumbnail

st.set_page_config(page_title="3 - QnA", layout="wide")
st.title("3 — Q&A (Slide-specific questions)")

# ------------------------------------------------------------
# Session state safety
# ------------------------------------------------------------
st.session_state.setdefault("generation_payload", None)
st.session_state.setdefault("questions_by_slide", {})
st.session_state.setdefault("answers_by_slide", {})

payload = st.session_state.get("generation_payload")
if not payload:
    st.warning("No slide selection found. Please select slides first.")
    st.stop()

slides = payload.get("selected_slides", [])
if not slides:
    st.warning("No slides selected.")
    st.stop()

# ------------------------------------------------------------
# Helper: generate questions from LLM (PLAIN TEXT)
# ------------------------------------------------------------
def generate_questions_for_slide(slide):
    slide_text = slide.get("full_text", "").strip()
    title = slide.get("title", "Untitled Slide")

    if not slide_text:
        return [
            "What key points should this slide cover?",
            "Any client-specific customization needed?",
            "Any metrics, numbers, or examples to include?"
        ]

    prompt = f"""
You are analysing a PowerPoint slide.

Slide title:
{title}

Slide content:
{slide_text}

Generate 3 to 5 clear, practical questions that a consultant should ask
a client in order to recreate or customize this slide.

Rules:
- Questions MUST be specific to this slide's content
- Do NOT return JSON
- Return one question per line
- No numbering, no bullets, no extra text
"""

    try:
        resp = text_client.responses.create(
            model=st.session_state.get("CHAT_MODEL"),
            input=prompt,
        )

        text = (resp.output_text or "").strip()
        if not text:
            raise ValueError("Empty LLM response")

        questions = [
            q.strip()
            for q in text.split("\n")
            if len(q.strip()) > 5
        ]

        if len(questions) < 2:
            raise ValueError("Too few questions generated")

        return questions[:5]

    except Exception as e:
        logger.exception("LLM question generation failed")
        return [
            "What key points should this slide cover?",
            "Any client-specific customization needed?",
            "Any important assumptions or constraints?"
        ]


# ------------------------------------------------------------
# UI Rendering
# ------------------------------------------------------------
st.info("Answer the questions below. Your answers will be used to generate the final PPT.")

for idx, slide in enumerate(slides, start=1):
    sid = slide["slide_id"]

    # ✅ HARD GUARANTEE STATE
    if sid not in st.session_state["answers_by_slide"]:
        st.session_state["answers_by_slide"][sid] = {}

    if sid not in st.session_state["questions_by_slide"]:
        st.session_state["questions_by_slide"][sid] = generate_questions_for_slide(slide)

    questions = st.session_state["questions_by_slide"][sid]

    st.markdown("---")
    cols = st.columns([1, 3])

    # --------------------------------------------------------
    # Left: slide thumbnail
    # --------------------------------------------------------
    with cols[0]:
        try:
            thumb = render_slide_thumbnail(slide)
            st.image(thumb, use_container_width=True)
        except Exception:
            st.caption("Slide preview unavailable")

    # --------------------------------------------------------
    # Right: questions + answers
    # --------------------------------------------------------
    with cols[1]:
        st.subheader(f"Slide {idx}: {slide.get('title', 'Untitled')}")

        for q in questions:
            prev = st.session_state["answers_by_slide"][sid].get(q, "")
            ans = st.text_area(
                q,
                value=prev,
                key=f"{sid}_{hash(q)}",
                height=90,
            )
            st.session_state["answers_by_slide"][sid][q] = ans


# ------------------------------------------------------------
# Save & Continue
# ------------------------------------------------------------
if st.button("Continue to Generate PPT ➡️"):
    st.session_state["generation_payload"] = {
        "selected_slides": slides,
        "answers_map": st.session_state["answers_by_slide"],
    }
    st.switch_page("pages/4_Generate_PPT.py")
