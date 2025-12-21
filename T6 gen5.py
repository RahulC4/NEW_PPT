# pages/5_Generate_PPT.py
import os
import tempfile
import streamlit as st

from generate_ppt_llm import generate_presentation
from azure_blob_utils import upload_ppt_to_blob
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("5 — Generate & Download PPT")

# --------------------------------------------------
# Load payload
# --------------------------------------------------
payload = st.session_state.get("generation_payload")

if not payload:
    st.warning("No generation payload found. Please complete previous steps.")
    st.stop()

# --------------------------------------------------
# 🔑 Apply preview edits if present
# --------------------------------------------------
preview_slides = payload.get("preview_slides")

if preview_slides:
    slides = []
    answers_map = {}

    for slide in preview_slides:
        slide_index = str(slide["slide_index"])

        slides.append({
            "slide_index": slide_index,
            "slide_title": slide["title"]
        })

        answers_map[slide_index] = {
            f"Bullet {i+1}": b
            for i, b in enumerate(slide.get("bullets", []))
            if b.strip()
        }

    payload = {
        "slides": slides,
        "answers_map": answers_map
    }

st.write("Generating final PowerPoint using edited slide content...")

# --------------------------------------------------
# Generate → Upload to Blob → Download
# --------------------------------------------------
try:
    # Generate PPT (returns temp/local file path)
    local_ppt_path = generate_presentation(payload)

    # Blob naming
    blob_name = os.path.basename(local_ppt_path)
    container_name = "generated-ppts"

    # Upload to Azure Blob Storage
    upload_ppt_to_blob(
        local_ppt_path,
        blob_name=blob_name,
        container_name=container_name
    )

    st.success("✅ PPT generated and uploaded to Azure Blob Storage!")
    st.markdown(f"**Blob container:** `{container_name}`")
    st.markdown(f"**File name:** `{blob_name}`")

    # Allow user to download from temp file (optional UX)
    with open(local_ppt_path, "rb") as f:
        st.download_button(
            label="⬇️ Download PPT",
            data=f,
            file_name=blob_name,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    # Cleanup local temp file
    try:
        os.remove(local_ppt_path)
    except Exception:
        logger.warning("Could not delete temp PPT file")

except Exception as e:
    logger.exception("PPT generation/upload failed")
    st.error(f"Failed to generate PPT: {e}")

# --------------------------------------------------
# Navigation
# --------------------------------------------------
st.markdown("---")

if st.button("⬅ Back to Preview"):
    st.switch_page("pages/4_📝_Preview_Slides.py")

if st.button("🏠 Back to Home"):
    st.switch_page("pages/1_Home.py")
