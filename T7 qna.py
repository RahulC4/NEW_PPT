# pages/3_❓_QnA.py
import streamlit as st
import json
from utils import text_client, get_env, safe_json_load, logger

st.set_page_config(page_title="3 - QnA", layout="wide")
st.title("3 — Q&A: Answer questions for selected slides")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def infer_title_and_text(slide):
    """
    Infer slide title and combined content from editable shapes.
    Compatible with slide_renderer output.
    """
    shapes = slide.get("editable_shapes", [])

    if shapes:
        title = shapes[0].get("text", "").strip()[:120]
        content = "\n".join(s.get("text", "") for s in shapes if s.get("text"))
    else:
        title = f"Slide {slide.get('slide_index', '')}"
        content = ""

    return title, content


def ask_llm_for_questions(title, content):
    """
    Ask LLM to generate generic, business-oriented questions for a slide.
    """
    system_prompt = (
        "You are analyzing a reference presentation slide. "
        "Generate 3 to 5 generic business questions that help recreate "
        "this slide for a new client. Ask about lists, scope, data points, "
        "assumptions, or key messages. "
        "Return JSON only in this format: {\"questions\": [\"...\"]}"
    )

    user_payload = {
        "slide_title": title,
        "slide_content": content
    }

    try:
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, indent=2)}
            ],
            temperature=0.2,
            max_completion_tokens=500
        )

        raw = resp.choices[0].message.content.strip()
        parsed = safe_json_load(raw)

        if isinstance(parsed, dict) and isinstance(parsed.get("questions"), list):
            return parsed["questions"]

    except Exception:
        logger.exception("LLM question generation failed")

    # Fallback
    return [
        "What key points should be covered in this slide?",
        "Are there any specific details or data to include?",
        "Any assumptions or exclusions to mention?"
    ]


# -------------------------------------------------
# Load selected slides (CRITICAL FIX)
# -------------------------------------------------
selected_slides = st.session_state.get("selected_slide_structs", [])

if not selected_slides:
    st.warning("No slides selected. Go back to Slide Selection.")
    st.stop()

st.session_state.setdefault("answers_by_slide", {})

# -------------------------------------------------
# Render QnA per slide
# -------------------------------------------------
for slide in selected_slides:

    slide_id = slide["slide_id"]
    title, content = infer_title_and_text(slide)

    st.subheader(title)
    st.image(slide.get("png_path"), use_container_width=True)

    # Generate questions once per slide
    qkey = f"questions_{slide_id}"
    if qkey not in st.session_state:
        st.session_state[qkey] = ask_llm_for_questions(title, content)

    questions = st.session_state[qkey]

    slide_answers = {}
    for i, q in enumerate(questions):
        slide_answers[q] = st.text_area(
            q,
            key=f"{slide_id}_q_{i}",
            height=80
        )

    st.session_state["answers_by_slide"][slide_id] = {
        "title": title,
        "answers": slide_answers
    }

    st.markdown("---")

# -------------------------------------------------
# Navigation
# -------------------------------------------------
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
