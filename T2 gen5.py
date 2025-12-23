import os
import streamlit as st
from datetime import datetime
from pptx import Presentation
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("Step 5 — Generate Your Presentation")

# ------------------------------------------------------------
# SAFE SESSION INIT (DO NOT RESET ON RERUN)
# ------------------------------------------------------------
if "generated_ppts" not in st.session_state:
    st.session_state["generated_ppts"] = []

payload = st.session_state.get("generation_payload")
theme = st.session_state.get("ppt_theme", "auto")

if not payload:
    st.warning("No generation payload found. Complete Q&A first.")
    st.stop()

st.write("Generating final PPT...")

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def extract_title_from_ppt(ppt_path: str) -> str:
    try:
        prs = Presentation(ppt_path)
        if prs.slides and prs.slides[0].shapes.title:
            return prs.slides[0].shapes.title.text.strip()
    except Exception:
        pass
    return "Generated_Presentation"


# ------------------------------------------------------------
# GENERATE PPT
# ------------------------------------------------------------
try:
    if theme == "cognizant":
        from generate_ppt_cognizant import generate_presentation_cognizant
        ppt_path = generate_presentation_cognizant(payload)
    else:
        from generate_ppt_llm import generate_presentation
        ppt_path = generate_presentation(payload)

    # --------------------------------------------------------
    # RENAME FILE (TITLE + TIMESTAMP)
    # --------------------------------------------------------
    ppt_title = extract_title_from_ppt(ppt_path)

    timestamp = datetime.now().strftime("%d_%b_%H-%M")
    safe_title = "".join(
        c for c in ppt_title if c.isalnum() or c in (" ", "_", "-")
    ).strip().replace(" ", "_")

    display_name = f"{safe_title}_{timestamp}.pptx"

    # --------------------------------------------------------
    # STORE IN SESSION (LATEST FIRST)
    # --------------------------------------------------------
    st.session_state["generated_ppts"].insert(
        0,
        {
            "path": ppt_path,
            "name": display_name,
            "created_at": datetime.now(),
        }
    )

    st.success("PPT generated successfully!")

except Exception as e:
    logger.exception("Generation failed")
    st.error(f"Failed to generate PPT: {e}")
    st.stop()

# ------------------------------------------------------------
# GENERATED PPTs (CURRENT SESSION)
# ------------------------------------------------------------
st.markdown("---")
st.subheader("📂 Generated PPTs (This Session)")

if not st.session_state["generated_ppts"]:
    st.caption("No PPTs generated yet.")
else:
    for idx, item in enumerate(st.session_state["generated_ppts"]):
        col1, col2 = st.columns([4, 2])

        with col1:
            st.write(f"{idx + 1}. {item['name']}")

        with col2:
            try:
                with open(item["path"], "rb") as f:
                    st.download_button(
                        label="⬇️ Download",
                        data=f,
                        file_name=item["name"],
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        key=f"download_{idx}",
                    )
            except Exception:
                st.caption("File not found on disk")

# ------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------
if st.button("Back to Home"):
    st.switch_page("pages/1_Home.py")
