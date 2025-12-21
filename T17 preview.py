# pages/4_Preview_Slides.py
import streamlit as st
import html
from utils import logger
import json
import hashlib

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

# ------------------------------------------------------------------
# Load payload from QnA (UNCHANGED STRUCTURE)
# ------------------------------------------------------------------
payload = st.session_state.get("generation_payload")

if not payload:
    st.error("No generation payload found. Please complete Q&A first.")
    st.stop()

slides = payload.get("slides", [])
answers_map = payload.get("answers_map", {})

# ------------------------------------------------------------------
# Signature to invalidate preview when Q&A or slides change
# ------------------------------------------------------------------
def _answers_signature(slides, answers_map):
    payload_sig = []
    for s in slides:
        idx = str(s["slide_index"])
        payload_sig.append({
            "slide_index": idx,
            "answers": answers_map.get(idx, {})
        })
    raw = json.dumps(payload_sig, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()

current_signature = _answers_signature(slides, answers_map)

if st.session_state.get("_preview_signature") != current_signature:
    st.session_state.pop("preview_slides", None)
    st.session_state["_preview_signature"] = current_signature

# ------------------------------------------------------------------
# Generate preview ONCE per payload (UNCHANGED LOGIC)
# ------------------------------------------------------------------
if "preview_slides" not in st.session_state:
    preview_slides = []

    from generate_ppt_llm import llm_synthesize_slide
    global_prompt = "professional business presentation"

    for slide in slides:
        idx = str(slide["slide_index"])
        slide_title = slide["slide_title"]
        user_answers = answers_map.get(idx, {})

        # Title slide
        if "What should be the title of this presentation?" in user_answers:
            title = user_answers["What should be the title of this presentation?"].strip()
            bullets = []

        else:
            has_valid_answers = any(v and v.strip() for v in user_answers.values())
            if not has_valid_answers:
                title = slide_title
                bullets = []
            else:
                try:
                    _, bullets = llm_synthesize_slide(user_answers, global_prompt)
                    title = slide_title
                except Exception:
                    logger.exception("Preview generation failed")
                    title = slide_title
                    bullets = []

        preview_slides.append({
            "title": title,
            "bullets": bullets
        })

    st.session_state["preview_slides"] = preview_slides

# ------------------------------------------------------------------
# PPT-LIKE VISUAL STYLES (UI ONLY)
# ------------------------------------------------------------------
st.markdown("""
<style>
.preview-slide {
    width: 1280px;
    height: 720px;
    margin: 40px auto;
    padding: 64px 72px;
    background: #ffffff;
    border-radius: 6px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.12);
    font-family: "Segoe UI", Arial, sans-serif;
}

.preview-title {
    font-size: 42px;
    font-weight: 600;
    margin-bottom: 36px;
    outline: none;
}

.preview-bullets {
    font-size: 22px;
    line-height: 1.6;
    padding-left: 28px;
}

.preview-bullets li {
    margin-bottom: 12px;
    outline: none;
}

.preview-title:focus,
.preview-bullets li:focus {
    outline: 2px solid #4c9aff;
    outline-offset: 4px;
}

.add-bullet {
    margin-top: 18px;
    color: #4c9aff;
    cursor: pointer;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Slide Renderer (HTML CANVAS)
# ------------------------------------------------------------------
def render_slide(title, bullets):
    bullets_html = "".join(
        f"<li contenteditable='true'>{html.escape(b)}</li>"
        for b in bullets
    )

    slide_html = f"""
    <div class="preview-slide">
        <div class="preview-title" contenteditable="true">
            {html.escape(title)}
        </div>

        <ul class="preview-bullets">
            {bullets_html}
        </ul>

        <div class="add-bullet" onclick="
            const ul = this.previousElementSibling;
            const li = document.createElement('li');
            li.setAttribute('contenteditable','true');
            li.innerText = 'New bullet';
            ul.appendChild(li);
            li.focus();
        ">
            + Add bullet
        </div>
    </div>
    """

    st.components.v1.html(slide_html, height=760)

# ------------------------------------------------------------------
# RENDER PREVIEW
# ------------------------------------------------------------------
st.subheader("🖥️ Slide Preview (Editable)")

for slide in st.session_state["preview_slides"]:
    render_slide(slide["title"], slide["bullets"])

# ------------------------------------------------------------------
# NAVIGATION (UNCHANGED)
# ------------------------------------------------------------------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Q&A"):
        st.switch_page("pages/3_❓_QnA.py")

with col2:
    if st.button("🎯 Generate PPT"):
        payload["slides"] = st.session_state["preview_slides"]
        st.session_state["generation_payload"] = payload
        st.switch_page("pages/5_Generate_PPT.py")
