# pages/4_Preview_Slides.py
import streamlit as st
import html
from utils import logger

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
# If preview not generated yet → generate ONCE using existing logic
# ------------------------------------------------------------------
if "preview_slides" not in st.session_state:
    preview_slides = []

    from generate_ppt_llm import llm_synthesize_slide

    global_prompt = "professional business presentation"

    for slide in slides:
        idx = str(slide["slide_index"])
        slide_title = slide["slide_title"]
        user_answers = answers_map.get(idx, {})

        # CASE: Title slide
        if "What should be the title of this presentation?" in user_answers:
            title = user_answers[
                "What should be the title of this presentation?"
            ].strip()
            bullets = []
        else:
            # LLM generates preview content
            try:
                llm_title, bullets = llm_synthesize_slide(
                    user_answers,
                    global_prompt
                )
                title = slide_title
            except Exception:
                logger.exception("Preview generation failed")
                title = slide_title
                bullets = ["Content could not be generated"]

        preview_slides.append({
            "title": title,
            "bullets": bullets
        })

    st.session_state["preview_slides"] = preview_slides

# ------------------------------------------------------------------
# HTML + CSS (REAL PPT LOOK)
# ------------------------------------------------------------------
st.markdown("""
<style>
.ppt-slide {
    width: 100%;
    border: 1px solid #ddd;
    padding: 28px;
    margin-bottom: 30px;
    background: white;
    font-family: "Segoe UI", sans-serif;
}

.ppt-title {
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 16px;
}

.ppt-bullets {
    font-size: 18px;
    padding-left: 22px;
}

.ppt-bullets li {
    margin-bottom: 10px;
}

.ppt-title:focus,
.ppt-bullets li:focus {
    outline: 2px solid #4c9aff;
}

.add-bullet {
    margin-top: 12px;
    color: #4c9aff;
    cursor: pointer;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Slide Renderer
# ------------------------------------------------------------------
def render_slide(slide_idx, title, bullets):
    bullets_html = "".join(
        f"<li contenteditable='true'>{html.escape(b)}</li>"
        for b in bullets
    )

    slide_html = f"""
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
    """

    st.components.v1.html(slide_html, height=420)

# ------------------------------------------------------------------
# RENDER PREVIEW
# ------------------------------------------------------------------
st.subheader("🖥️ Slide Preview (Editable)")

for i, slide in enumerate(st.session_state["preview_slides"], start=1):
    render_slide(i, slide["title"], slide["bullets"])

# ------------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("⬅ Back to Q&A"):
        st.switch_page("pages/3_❓_QnA.py")

with col2:
    if st.button("🎯 Generate PPT"):
        # 🔑 IMPORTANT: use preview slides as final source
        payload["slides"] = st.session_state["preview_slides"]
        st.session_state["generation_payload"] = payload
        st.switch_page("pages/5_Generate_PPT.py")
