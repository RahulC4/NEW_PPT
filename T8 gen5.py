# pages/5_Generate_PPT.py
import os
import streamlit as st
from generate_ppt_llm import generate_presentation
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("5 — Generate & Download PPT")

preview = st.session_state.get("preview_slides")

if not preview:
    st.error("No preview content found.")
    st.stop()

try:
    out_path = generate_presentation({
        "preview_slides": preview
    })

    st.success("PPT generated successfully!")

    with open(out_path, "rb") as f:
        st.download_button(
            "⬇️ Download PPT",
            f,
            file_name=os.path.basename(out_path),
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

except Exception as e:
    logger.exception("PPT generation failed")
    st.error(str(e))
