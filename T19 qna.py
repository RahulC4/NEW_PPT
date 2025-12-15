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
    "Questions are generated based on slide type:\n"
    "- Title slide → title question\n"
    "- Agenda slide → agenda items\n"
    "- Content slide → objective + AI questions + key points\n"
    "- Thank You slide → no questions"
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def is_title_slide(title: str):
    return title.strip().lower() in ["title", "cover", "introduction"]

def is_agenda_slide(title: str):
    return "agenda" in title.lower()

def is_thankyou_slide(title: str):
    return "thank" in title.lower()

# ------------------------------------------------------------------
# LLM QUESTIONS (CONTENT SLIDES ONLY)
# ------------------------------------------------------------------
def generate_llm_questions(slide):
    slide_title = slide.get("title", "")
    slide_index = slide.get("slide_index", "")

    query = f"Slide {slide_index}: {slide_title}"
    results = semantic_search(query=query, top_k=3)

    if not results:
        return []

    context = "\n".join(
        r.get("text", "")[:600] for r in results if r.get("text")
    ).strip()

    if not context:
        return []

    prompt = f"""
You are analyzing a PowerPoint content slide.

SLIDE TITLE:
{slide_title}

REFERENCE CONTENT:
{context}

TASK:
Generate up to 3 specific, non-generic clarification questions
about this slide.

Rules:
- No objectives or key points questions
- Plain numbered list
- Keep questions short
"""

    resp = text_client.chat.completions.create(
        model=get_env("CHAT_MODEL", required=True),
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=250
    )

    raw = resp.choices[0].message.content or ""
    questions = []

    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit():
            q = line.split(".", 1)[-1].strip()
            if q:
                questions.append(q)

    return questions[:3]

# ------------------------------------------------------------------
# Generate questions per slide
# ------------------------------------------------------------------
for slide in slides:
    qkey = f"qna_final_{slide['slide_id']}"
    if qkey in st.session_state:
        continue

    title = slide.get("title", "")
    questions = []

    if is_title_slide(title):
        questions = ["What should be the title of this presentation?"]

    elif is_agenda_slide(title):
        questions = ["What topics should be included in the agenda?"]

    elif is_thankyou_slide(title):
        questions = []

    else:
        # Content slide
        questions.append("What is the objective of this slide?")

        llm_qs = generate_llm_questions(slide)
        questions.extend(llm_qs)

        questions.append("What are the key points to be added to this slide?")

    st.session_state[qkey] = questions

# ------------------------------------------------------------------
# Display Q&A UI
# ------------------------------------------------------------------
st.session_state.setdefault("answers_by_slide", {})

for s_idx, slide in enumerate(slides):
    slide_id = slide["slide_id"]
    qkey = f"qna_final_{slide_id}"
    questions = st.session_state.get(qkey, [])

    st.markdown("---")
    st.subheader(f"Slide {s_idx + 1}: {slide.get('title', 'Untitled Slide')}")

    # ✅ Thumbnail reduced to ~50%
    if slide.get("png_path") and os.path.exists(slide["png_path"]):
        st.image(slide["png_path"], width=420)

    st.session_state["answers_by_slide"].setdefault(slide_id, {})

    for q_idx, q in enumerate(questions):
        # ✅ collision-proof key
        widget_key = f"slide_{s_idx}_q_{q_idx}"

        val = st.text_area(
            label=q,
            value=st.session_state["answers_by_slide"][slide_id].get(q, ""),
            key=widget_key,
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
            idx = str(slide["slide_index"])
            answers_for_generator[idx] = st.session_state["answers_by_slide"].get(
                slide["slide_id"], {}
            )

        st.session_state["generation_payload"] = {
            "selected_slides": slides,
            "answers_map": answers_for_generator
        }
        st.switch_page("pages/4_Generate_PPT.py")
