import os
import streamlit as st
from datetime import datetime
from pptx import Presentation
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("Step 5 — Generate Your Presentation")

# ------------------------------------------------------------
# SAFE SESSION INIT (DO NOT RESET)
# ------------------------------------------------------------
if "generated_ppts" not in st.session_state:
    st.session_state["generated_ppts"] = []

payload = st.session_state.get("generation_payload")
theme = st.session_state.get("ppt_theme", "auto")

if not payload:
    st.warning("No generation payload found. Please complete preview first.")
    st.stop()

st.info("Generating final PPT...")

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def extract_title_from_ppt(ppt_path: str) -> str:
    try:
        prs = Presentation(ppt_path)
        if prs.slides and prs.slides[0].shapes.title:
            title = prs.slides[0].shapes.title.text.strip()
            if title:
                return title
    except Exception:
        pass
    return "Generated_Presentation"


def already_added(path: str) -> bool:
    return any(p["path"] == path for p in st.session_state["generated_ppts"])


# ------------------------------------------------------------
# GENERATE PPT (ONLY ON PAGE LOAD FROM PREVIEW)
# ------------------------------------------------------------
try:
    if theme == "cognizant":
        from generate_ppt_cognizant import generate_presentation_cognizant
        out_path = generate_presentation_cognizant(payload)
    else:
        from generate_ppt_llm import generate_presentation
        out_path = generate_presentation(payload)

    # --------------------------------------------------------
    # SESSION INSERT (ONCE, THEME-AGNOSTIC)
    # --------------------------------------------------------
    if not already_added(out_path):
        ppt_title = extract_title_from_ppt(out_path)
        timestamp = datetime.now().strftime("%d_%b_%H-%M")
        display_name = f"{ppt_title}_{timestamp}.pptx"

        st.session_state["generated_ppts"].insert(
            0,
            {
                "path": out_path,
                "name": display_name,
                "created_at": datetime.now(),
            },
        )

    st.success("PPT generated successfully!")

except Exception as e:
    logger.exception("PPT generation failed")
    st.error(f"Failed to generate PPT: {e}")
    st.stop()

# ------------------------------------------------------------
# GENERATED PPTs (THIS SESSION)
# ------------------------------------------------------------
st.markdown("---")
st.subheader("📂 Generated PPTs (This Session)")

if not st.session_state["generated_ppts"]:
    st.caption("No PPTs generated yet.")
else:
    for idx, item in enumerate(st.session_state["generated_ppts"], start=1):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{idx}. {item['name']}")
        with col2:
            with open(item["path"], "rb") as f:
                st.download_button(
                    label="⬇️ Download",
                    data=f,
                    file_name=item["name"],
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    key=f"download_{idx}",
                )

# ------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------
st.markdown("---")
if st.button("⬅️ Back to Home"):
    st.switch_page("pages/1_Home.py")
