import os
import streamlit as st
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("Step 5 — Generate Your Presentation")

payload = st.session_state.get("generation_payload")
theme = st.session_state.get("ppt_theme", "auto")

if not payload:
    st.warning("No generation payload found. Complete Q&A first.")
    st.stop()

st.write("Generating final PPT...")

try:
    if theme == "cognizant":
        from generate_ppt_cognizant import generate_presentation_cognizant
        out_path = generate_presentation_cognizant(payload)
    else:
        from generate_ppt_llm import generate_presentation
        out_path = generate_presentation(payload)
    

    st.success("PPT generated successfully!")
    st.markdown(f"**File:** `{os.path.basename(out_path)}`")

    with open(out_path, "rb") as f:
        st.download_button(
            "⬇️ Download PPT",
            f,
            file_name=os.path.basename(out_path),
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

except Exception as e:
    logger.exception("Generation failed")
    st.error(f"Failed to generate PPT: {e}")

if st.button("Back to Home"):
    st.switch_page("pages/1_Home.py")
