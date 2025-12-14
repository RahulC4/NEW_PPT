# pages/3_❓_QnA.py
import streamlit as st
from utils import text_client, get_env, logger
from search_utils import semantic_search

st.set_page_config(page_title="3 - QnA", layout="wide")
st.title("3 — Q&A (Slide Understanding)")

# ------------------------------------------------------------------
# Load selected slides
# ------------------------------------------------------------------
slides = st.session_state.get("selected_slide_structs", [])
if not slides:
    st.error("No slides selected. Go back to Slide Selection.")
    st.stop()

st.info(
    "The AI analyzes the selected slide content (from the dataset) "
    "and asks 3–5 relevant questions to generate new slide content."
)

# ------------------------------------------------------------------
# Helper: get slide text from Chroma (IMPORTANT)
# ------------------------------------------------------------------
def get_slide_context_from_chroma(slide):
    """
    Fetch richer slide text from Chroma using ppt_name + slide_id
    """
    slide_id = slide.get("slide_id")
    ppt_name = slide.get("ppt_blob")

    query = f"{ppt_name} {slide_id}"
    results = semantic_search(query, top_k=3)

    texts = []
    for r in results:
        if r.get("text"):
            texts.append(r["text"])

    return "\n".join(texts).strip()


# ------------------------------------------------------------------
# LLM: generate numbered questions (NO JSON)
# ------------------------------------------------------------------
def generate_questions(slide_context, slide_title):
    prompt = f"""
You are analyzing a PowerPoint slide from a proposal deck.

Slide title:
{slide_title}

Slide content:
{slide_context}

TASK:
Generate 3 to 5 short, specific, non-generic questions
that help customize or rewrite this slide for a new client.

Rules:
- Questions MUST be based on the slide content
- Ask about scope, LOBs, key points, assumptions, metrics, or deliverables
- Return ONLY numbered questions, one per line
- Do NOT add explanations

Example:
1. Which lines of business should be included?
2. Any client-specific customization required?
3. What key outcomes should be highlighted?
"""

    resp = text_client.chat.completions.create(
        model=get_env("CHAT_MODEL", required=True),
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=400
    )

    raw = resp.choices[0].message.content or ""
    raw = raw.strip()

    if not raw:
        raise RuntimeError("LLM returned empty response")

    questions = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit():
            questions.append(line.split(".", 1)[-1].strip())

    if not questions:
        raise RuntimeError(f"Could not parse questions:\n{raw}")

    return questions


# ------------------------------------------------------------------
# Generate questions ONCE per slide
# ------------------------------------------------------------------
st.session_state.setdefault("questions_by_slide", {})
st.session_state.setdefault("answers_by_slide", {})

for slide in slides:
    sid = slide["slide_id"]
    if sid not in st.session_state["questions_by_slide"]:
        try:
            context = get_slide_context_from_chroma(slide)
            if not context:
                raise RuntimeError("No slide context found in Chroma")

            qs = generate_questions(context, slide.get("title", ""))
            st.session_state["questions_by_slide"][sid] = qs
            st.session_state["answers_by_slide"].setdefault(sid, {})
        except Exception as e:
            logger.exception("Question generation failed")
            st.session_state["questions_by_slide"][sid] = [f"ERROR: {e}"]


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------
for idx, slide in enumerate(slides):
    sid = slide["slide_id"]
    st.markdown("---")
    st.subheader(f"Slide {idx+1}: {slide.get('title','Untitled Slide')}")

    questions = st.session_state["questions_by_slide"].get(sid, [])

    for q in questions:
        ans = st.text_area(
            q,
            value=st.session_state["answers_by_slide"][sid].get(q, ""),
            key=f"{sid}_{q}"
        )
        st.session_state["answers_by_slide"][sid][q] = ans


# ------------------------------------------------------------------
# Navigation
# ------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Slide Selection"):
        st.switch_page("pages/2_🖼️_Slide_Selection.py")

with col2:
    if st.button("➡ Generate PPT"):
        st.session_state["generation_payload"] = {
            "selected_slides": slides,
            "answers_map": st.session_state["answers_by_slide"]
        }
        st.switch_page("pages/4_Generate_PPT.py")
