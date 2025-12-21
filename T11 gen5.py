# pages/5_Generate_PPT.py
import os
import streamlit as st
from generate_ppt_llm import generate_presentation
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("5 — Generate & Download")

payload = st.session_state.get("generation_payload")

if not payload:
    st.warning("No generation payload found.")
    st.stop()

if "preview_slides" in payload:
    payload["slides"] = payload["preview_slides"]

try:
    out_path = generate_presentation(payload)

    st.success("PPT generated successfully!")
    st.download_button(
        "⬇️ Download PPT",
        open(out_path, "rb"),
        file_name=os.path.basename(out_path),
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

except Exception as e:
    logger.exception("Generation failed")
    st.error(f"Failed to generate PPT: {e}")

if st.button("Back to Home"):
    st.switch_page("pages/1_Home.py")
