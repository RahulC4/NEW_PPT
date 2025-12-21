# pages/5_Generate_PPT.py
import os
import streamlit as st
from generate_ppt_llm import generate_presentation
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("5 — Generate & Download")

payload = st.session_state.get("generation_payload")
if not payload:
    st.error("No generation payload found.")
    st.stop()

# ---------------------------------------------------
# OVERRIDE WITH PREVIEW CONTENT (KEY FIX)
# ---------------------------------------------------
preview = payload.get("preview_slides")
if preview:
    payload["slides"] = [
        {
            "slide_index": s["slide_index"],
            "slide_title": s["title"],
            "bullets": s["bullets"]
        }
        for s in preview
    ]

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
    st.error(str(e))
