# pages/3_❓_QnA.py
import os
import json
import streamlit as st
from utils import text_client, get_env, safe_json_load, logger

st.set_page_config(page_title="3 - Q&A", layout="wide")
st.title("3 — Q&A (Slide-aware questions)")

selected_slides = st.session_state.get("selected_slide_structs")

if not selected_slides:
    st.warning("No slides selected. Go back to Slide Selection.")
    st.stop()

st.info(
    "Answer slide-specific questions below. "
    "Your answers will be used to generate slide content (not copy designs)."
)

# -----------------------------
# LLM QUESTION GENERATION
# -----------------------------
def generate_slide_questions(slide):
    """
    Ask LLM to analyze the slide and generate meaningful questions.
    Output format:
    {
      "questions": [
        {"id": "q1", "question": "..."},
        {"id": "q2", "question": "..."}
      ]
    }
    """

    slide_context = {
        "slide_title": slide.get("title"),
        "slide_text": slide.get("text"),
        "slide_index": slide.get("slide_index"),
    }

    system_prompt = (
        "You are a senior presentation consultant.\n"
        "Analyze the given slide content and infer the slide intent "
        "(e.g., Overview, Scope, LOBs, Approach, Benefits, Timeline, Risks, Summary).\n\n"
        "Generate 3–6 intelligent, business-relevant questions that help create "
        "new slide content for a DIFFERENT client.\n\n"
        "Rules:\n"
        "- Questions must NOT be generic\n"
        "- Do NOT repeat slide text\n"
        "- Prefer questions like:\n"
        "  • Which LOBs are required?\n"
        "  • What scope should be included?\n"
        "  • Any key differentiators?\n"
        "  • What bullets should appear on this slide?\n"
        "- Output JSON ONLY in the specified format\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "Slide data:\n" + json.dumps(slide_context, indent=2),
        },
    ]

    try:
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=messages,
            temperature=0.3,
            max_completion_tokens=700,
        )

        raw = resp.choices[0].message.content.strip()
        parsed = safe_json_load(raw)

        if isinstance(parsed, dict) and "questions" in parsed:
            return parsed["questions"]

    except Exception:
        logger.exception("LLM failed to generate questions")

    # Fallback (very minimal)
    return [
        {"id": "q1", "question": "What key points should this slide cover?"},
        {"id": "q2", "question": "Any client-specific customization needed?"},
    ]


# -----------------------------
# INITIALIZE SESSION STATE
# -----------------------------
st.session_state.setdefault("qa_questions", {})
st.session_state.setdefault("qa_answers", {})

# Generate questions once
for slide in selected_slides:
    sid = str(slide["slide_index"])
    if sid not in st.session_state["qa_questions"]:
        st.session_state["qa_questions"][sid] = generate_slide_questions(slide)
        st.session_state["qa_answers"][sid] = {}

# -----------------------------
# RENDER UI
# -----------------------------
for slide in selected_slides:
    sid = str(slide["slide_index"])

    st.markdown(f"## Slide {slide['slide_index'] + 1}: {slide.get('title','')}")
    if slide.get("png_path"):
        st.image(slide["png_path"], use_container_width=True)

    for q in st.session_state["qa_questions"].get(sid, []):
        qid = q["id"]
        key = f"ans_{sid}_{qid}"

        answer = st.text_area(
            q["question"],
            key=key,
            value=st.session_state["qa_answers"][sid].get(qid, ""),
            height=80,
        )

        st.session_state["qa_answers"][sid][qid] = answer

    st.markdown("---")

# -----------------------------
# CONTINUE TO GENERATION
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Generate PPT"):
        st.session_state["generation_payload"] = {
            "selected_slides": selected_slides,
            "answers_map": st.session_state["qa_answers"],
        }
        st.switch_page("pages/4_Generate_PPT.py")

with col2:
    if st.button("Back to Slide Selection"):
        st.switch_page("pages/2_🖼️_Slide_Selection.py")
