# pages/3_❓_QnA.py
import streamlit as st
import json
from utils import text_client, get_env, safe_json_load

st.set_page_config(page_title="3 - QnA", layout="wide")
st.title("3 — Q&A: Slide Intent Questions")

slides = st.session_state.get("selected_slide_structs", [])
if not slides:
    st.warning("No slides selected.")
    st.stop()

def ask_questions(slide):
    sys = (
        "You analyze a reference slide and ask 3–5 generic, intent-based questions "
        "to help recreate this slide for a new client. "
        "Questions should cover data like LOBs, key points, scope, assumptions."
        "Return JSON: {questions: [..]}"
    )
    user = {
        "title": slide["title"],
        "content": slide["text"]
    }

    resp = text_client.chat.completions.create(
        model=get_env("CHAT_MODEL", required=True),
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": json.dumps(user)}
        ],
        temperature=0.2,
        max_completion_tokens=400
    )

    parsed = safe_json_load(resp.choices[0].message.content)
    return parsed.get("questions", []) if parsed else []

for slide in slides:
    st.subheader(slide["title"])
    st.image(slide["preview_image"], use_container_width=True)

    qkey = f"questions_{slide['slide_id']}"
    if qkey not in st.session_state:
        st.session_state[qkey] = ask_questions(slide)

    answers = {}
    for i, q in enumerate(st.session_state[qkey]):
        answers[q] = st.text_area(q, key=f"{slide['slide_id']}_{i}")

    st.session_state.setdefault("answers_by_slide", {})
    st.session_state["answers_by_slide"][slide["slide_id"]] = {
        "title": slide["title"],
        "answers": answers
    }

    st.markdown("---")

if st.button("Generate PPT"):
    st.session_state["generation_payload"] = st.session_state["answers_by_slide"]
    st.switch_page("pages/4_Generate_PPT.py")
