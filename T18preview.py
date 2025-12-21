# pages/4_Preview_Slides.py
import streamlit as st
import html
from utils import logger
import json
import hashlib

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

# ------------------------------------------------------------------
# Load payload from QnA (UNCHANGED)
# ------------------------------------------------------------------
payload = st.session_state.get("generation_payload")
if not payload:
    st.error("No generation payload found. Please complete Q&A first.")
    st.stop()

slides = payload.get("slides", [])
answers_map = payload.get("answers_map", {})

# ------------------------------------------------------------------
# Signature for cache invalidation (UNCHANGED)
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
    from generate_ppt_llm import llm_synthesize_slide

    preview_slides = []
    global_prompt = "professional business presentation"

    for slide in slides:
        idx = str(slide["slide_index"])
        slide_title = slide["slide_title"]
        user_answers = answers_map.get(idx, {})

        # Case 1: Presentation title slide
        if "What should be the title of this presentation?" in user_answers:
            title = user_answers["What should be the title of this presentation?"].strip()
            bullets = []

        else:
            has_valid_answers = any(v and v.strip() for v in user_answers.values())

            # Case 2: No answers → title only
            if not has_valid_answers:
                title = slide_title
                bullets = []

            # Case 3: Normal LLM generation
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
# PPT-LIKE VISUAL STYLES (UPDATED UI ONLY)
# ------------------------------------------------------------------
st.markdown("""
<style>
.preview-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 50px;
}

.ppt-slide {
    width: 1280px;
    height: 720px;
    background: white;
    border: 1px solid #d0d0d0;
    padding: 64px;
    font-family: "Segoe UI", Arial, sans-serif;
    box-shadow: 0 6px 18px rgba(0,0,0,0.12);
}

.ppt-title {
    font-size: 40px;
    font-weight: 600;
    margin-bottom: 36px;
}

.ppt-bullets {
    font-size: 22px;
    line-height: 1.7;
    padding-left: 32px;
}

.ppt-bullets li {
    margin-bottom: 14px;
}

.ppt-title:focus,
.ppt-bullets li:focus {
    outline: 2px solid #4c9aff;
}

.add-bullet {
    margin-top: 18px;
    font-size: 18px;
    color: #4c9aff;
    cursor: pointer;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Slide Renderer (VISUAL CHANGE ONLY)
# ------------------------------------------------------------------
def render_slide(title, bullets):
    bullets_html = "".join(
        f"<li contenteditable='true'>{html.escape(b)}</li>"
        for b in bullets
    )

    slide_html = f"""
    <div class="preview-wrapper">
      <div class="ppt-slide">
        <div class="ppt-title" contenteditable="true">
            {html.escape(title)}
        </div>

        <ul class="ppt-bullets">
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
    </div>
    """

    st.components.v1.html(slide_html, height=780)

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
