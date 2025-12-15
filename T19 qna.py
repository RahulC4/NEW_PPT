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
    slide_title = slide_struct.get("title", "")
    slide_index = slide_struct.get("slide_index", "")

    query = f"Slide {slide_index}: {slide_title}".strip()
    if not query:
        raise ValueError("Missing slide title/index for Chroma query")

    # ---- Chroma Search ----
    results = semantic_search(query=query, top_k=3)
    if not results:
        raise RuntimeError(f"No indexed content found for slide: {query}")

    # Limit context size
    retrieved_text = "\n".join(
        r.get("text", "")[:800] for r in results if r.get("text")
    ).strip()

    if not retrieved_text:
        raise RuntimeError("Chroma returned empty text")

    prompt = f"""
You are analysing a PowerPoint slide.

SLIDE TITLE:
{slide_title}

REFERENCE CONTENT:
{retrieved_text}

TASK:
Ask exactly 3–5 clear, practical questions that help
customize or refine THIS slide.

Rules:
- Questions must be specific to the content
- No generic questions
- Plain numbered text only
- Always return something

Start now.
"""

    for _ in range(2):  # one retry
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=300
        )

        raw = resp.choices[0].message.content
        if raw and raw.strip():
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            questions = []
            for ln in lines:
                if ln[0].isdigit():
                    q = ln.split(".", 1)[-1].strip()
                    if q:
                        questions.append(q)
            if questions:
                return questions

    raise RuntimeError("LLM returned empty response after retry")


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
    st.subheader(f"Slide {idx + 1}: {slide.get('title', 'Untitled Slide')}")

    # ✅ Smaller thumbnail (about 50%)
    if slide.get("png_path") and os.path.exists(slide["png_path"]):
        st.image(
            slide["png_path"],
            width=450,  # 👈 reduced size
        )

    st.session_state["answers_by_slide"].setdefault(slide_id, {})

    for i, q in enumerate(questions):
        # ✅ FIX: collision-proof Streamlit key
        answer_key = f"slide_{idx}_q_{i}"

        val = st.text_area(
            label=q,
            value=st.session_state["answers_by_slide"][slide_id].get(q, ""),
            key=answer_key,
            height=80,
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
            idx_str = str(slide["slide_index"])
            answers_for_generator[idx_str] = st.session_state["answers_by_slide"].get(
                slide["slide_id"], {}
            )

        st.session_state["generation_payload"] = {
            "selected_slides": slides,
            "answers_map": answers_for_generator
        }
        st.switch_page("pages/4_Generate_PPT.py")
