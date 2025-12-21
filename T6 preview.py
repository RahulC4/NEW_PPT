# pages/4_📝_Preview_Slides.py
import streamlit as st

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

payload = st.session_state.get("generation_payload")

if not payload:
    st.warning("No generation payload found.")
    st.stop()

slides = payload.get("slides", [])
answers_map = payload.get("answers_map", {})

# --------------------------------------------------
# Init preview state ONCE
# --------------------------------------------------
st.session_state.setdefault("preview_slides", [])

if not st.session_state["preview_slides"]:
    for slide in slides:
        slide_idx = str(slide["slide_index"])
        answers = answers_map.get(slide_idx, {})

        bullets = [v for v in answers.values() if v.strip()]

        st.session_state["preview_slides"].append({
            "slide_index": slide_idx,
            "title": slide["slide_title"],
            "bullets": bullets or [""]
        })

# --------------------------------------------------
# Slide-like preview UI
# --------------------------------------------------
for i, slide in enumerate(st.session_state["preview_slides"]):
    st.markdown("---")

    with st.container():
        st.markdown(
            """
            <div style="
                border: 1px solid #ccc;
                padding: 30px;
                border-radius: 6px;
                background-color: #ffffff;
                min-height: 320px;
            ">
            """,
            unsafe_allow_html=True
        )

        # TITLE (looks like PPT title)
        slide["title"] = st.text_input(
            "Slide Title",
            value=slide["title"],
            key=f"title_{i}"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # BULLETS
        bullets = []
        for j, b in enumerate(slide["bullets"]):
            val = st.text_area(
                f"Bullet {j + 1}",
                value=b,
                height=40,
                key=f"bullet_{i}_{j}"
            )
            bullets.append(val)

        if st.button("➕ Add Bullet", key=f"add_{i}"):
            bullets.append("")

        slide["bullets"] = bullets

        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# Save edited preview → generator payload
# --------------------------------------------------
st.markdown("---")

if st.button("➡ Generate Final PPT"):
    st.session_state["generation_payload"]["preview_slides"] = (
        st.session_state["preview_slides"]
    )
    st.switch_page("pages/5_Generate_PPT.py")

if st.button("⬅ Back to Q&A"):
    st.switch_page("pages/3_❓_QnA.py")
