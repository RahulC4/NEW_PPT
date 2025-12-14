# pages/3_❓_QnA.py

import os
import streamlit as st
from utils import text_client, get_env, logger
from search_utils import semantic_search

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
    "The AI retrieves indexed content from the slide dataset and "
    "asks 3–5 relevant questions per slide."
)

# ------------------------------------------------------------------
# CHROMA → LLM QUESTION GENERATION (NO FALLBACK)
# ------------------------------------------------------------------
def generate_questions_for_slide(slide_struct):
    """
    1. Search Chroma DB for this slide
    2. Use retrieved content to generate questions
    """

    slide_title = slide_struct.get("title", "")
    slide_index = slide_struct.get("slide_index", "")

    query = f"Slide {slide_index}: {slide_title}".strip()
    if not query:
        raise ValueError("Missing slide title/index for Chroma query")

    # ---- Chroma Search ----
    results = semantic_search(
        query=query,
        top_k=5
    )

    if not results:
        raise RuntimeError(
            f"No indexed content found in Chroma for slide: {query}"
        )

    retrieved_text = "\n\n".join(
        r.get("text", "") for r in results if r.get("text")
    ).strip()

    if not retrieved_text:
        raise RuntimeError("Chroma returned empty text for this slide")

    # ---- LLM Prompt ----
    prompt = f"""
You are an expert PowerPoint consultant.

Below is indexed content retrieved from a reference slide dataset.

SLIDE CONTEXT:
{retrieved_text}

TASK:
Generate 3 to 5 highly relevant, slide-specific questions
that a user must answer to personalize or improve this slide.

Rules:
- Questions MUST be based on the content above
- Focus on business intent, scope, metrics, decisions, or assumptions
- NO generic questions
- NO JSON
- Output plain numbered text only (one question per line)

Example:
1. Which LOBs should be prioritized in this phase?
2. What metrics define success for this capability?
3. Are there regulatory constraints to highlight?
"""

    try:
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=400
        )

        raw = resp.choices[0].message.content.strip()
        if not raw:
            raise RuntimeError("LLM returned empty response")

        # ---- Parse numbered questions ----
        questions = []
        for ln in raw.splitlines():
            ln = ln.strip()
            if ln and ln[0].isdigit():
                q = ln.split(".", 1)[-1].strip()
                if q:
                    questions.append(q)

        if not questions:
            raise RuntimeError(
                f"No questions parsed from LLM output:\n{raw}"
            )

        return questions

    except Exception as e:
        logger.exception("QnA generation failed")
        raise RuntimeError(str(e))


# ------------------------------------------------------------------
# Generate questions once per slide
# ------------------------------------------------------------------
for slide in slides:
    qkey = f"qna_chroma_{slide['slide_id']}"
    if qkey not in st.session_state:
        st.session_state[qkey] = generate_questions_for_slide(slide)


# ------------------------------------------------------------------
# Display Q&A UI
# ------------------------------------------------------------------
st.session_state.setdefault("answers_by_slide", {})

for idx, slide in enumerate(slides):
    slide_id = slide["slide_id"]
    qkey = f"qna_chroma_{slide_id}"
    questions = st.session_state.get(qkey, [])

    st.markdown("---")
    st.subheader(f"Slide {idx+1}: {slide.get('title', 'Untitled Slide')}")

    # Preview image (if exists)
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
