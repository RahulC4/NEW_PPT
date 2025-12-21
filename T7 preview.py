# pages/4_Preview_Slides.py
import streamlit as st
import json
import uuid

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

payload = st.session_state.get("generation_payload")
if not payload:
    st.error("No generation payload found.")
    st.stop()

slides = payload["slides"]
answers_map = payload["answers_map"]

# ---------------------------------------------------
# INIT PREVIEW STATE (only once)
# ---------------------------------------------------
st.session_state.setdefault("preview_slides", [])

if not st.session_state["preview_slides"]:
    preview = []
    for s in slides:
        slide_idx = str(s["slide_index"])
        answers = answers_map.get(slide_idx, {})

        bullets = [
            a for a in answers.values()
            if a and a.strip() and "title" not in a.lower()
        ]

        preview.append({
            "slide_index": s["slide_index"],
            "title": s["slide_title"],
            "bullets": bullets[:5] or ["Click to edit bullet"]
        })

    st.session_state["preview_slides"] = preview

# ---------------------------------------------------
# RENDER SLIDES
# ---------------------------------------------------
for i, slide in enumerate(st.session_state["preview_slides"]):
    slide_id = f"slide_{i}_{uuid.uuid4().hex[:6]}"

    st.components.v1.html(
        f"""
        <div style="
            width:1280px;
            height:720px;
            border:1px solid #ccc;
            padding:60px;
            margin-bottom:40px;
            font-family:Arial;
            background:white;
        ">
            <div contenteditable="true"
                 id="{slide_id}_title"
                 style="
                    font-size:40px;
                    font-weight:600;
                    margin-bottom:30px;
                 ">
                {slide["title"]}
            </div>

            <ul style="font-size:22px;">
                {''.join([
                    f'<li contenteditable="true">{b}</li>'
                    for b in slide["bullets"]
                ])}
            </ul>
        </div>

        <script>
        const save = () => {{
            const title = document.getElementById("{slide_id}_title").innerText;
            const bullets = [...document.querySelectorAll("#{slide_id}_title ~ ul li")]
                .map(li => li.innerText);

            window.parent.postMessage({{
                slideIndex: {i},
                title,
                bullets
            }}, "*");
        }};

        document.addEventListener("input", save);
        </script>
        """,
        height=780,
    )

# ---------------------------------------------------
# RECEIVE EDITS FROM JS
# ---------------------------------------------------
if "preview_updates" not in st.session_state:
    st.session_state["preview_updates"] = {}

st.markdown(
    """
    <script>
    window.addEventListener("message", (event) => {
        const data = event.data;
        if (data.slideIndex !== undefined) {
            window.parent.streamlitSendMessage({
                type: "preview_update",
                data
            });
        }
    });
    </script>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# GENERATE BUTTON
# ---------------------------------------------------
if st.button("Generate PPT"):
    payload["preview_slides"] = st.session_state["preview_slides"]
    st.session_state["generation_payload"] = payload
    st.switch_page("pages/5_Generate_PPT.py")
