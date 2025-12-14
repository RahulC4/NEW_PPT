import os
import streamlit as st

from main_generator import generate_ppt
from storage.azure_blob_utils import (
    upload_source_ppt_to_blob,
    list_source_ppt_blobs,
)

# ------------------------------------------------------
# Streamlit Page Config
# ------------------------------------------------------
st.set_page_config(
    page_title="AI PPT Generator",
    layout="wide"
)

st.title("📊 AI PowerPoint Generator")
st.write("Generate presentations from your indexed PPT dataset using AI")

# ------------------------------------------------------
# Source PPT Dataset Section
# ------------------------------------------------------
st.header("📂 Source PPT Dataset")

uploaded_file = st.file_uploader(
    "Upload a source PPT (used only for ingestion & design reference)",
    type=["pptx"]
)

if uploaded_file:
    if st.button("Upload to Dataset"):
        with st.spinner("Uploading source PPT..."):
            upload_source_ppt_to_blob(
                uploaded_file.name,
                uploaded_file.read()
            )
        st.success("Source PPT uploaded successfully!")

st.subheader("Available Source PPTs")
ppt_list = list_source_ppt_blobs()
if ppt_list:
    for ppt in ppt_list:
        st.write(f"• {ppt}")
else:
    st.info("No source PPTs uploaded yet.")

# ------------------------------------------------------
# PPT Generation Section
# ------------------------------------------------------
st.header("✨ Generate New Presentation")

prompt = st.text_area(
    "Enter your presentation requirement",
    height=150,
    placeholder=(
        "Example:\n"
        "Create a proposal deck for CareSource covering:\n"
        "- Introduction\n"
        "- Problem statement\n"
        "- Proposed solution\n"
        "- Benefits\n"
        "- Conclusion"
    )
)

# ------------------------------------------------------
# Generate Button
# ------------------------------------------------------
if st.button("Generate PPT"):
    if not prompt.strip():
        st.warning("Please enter a prompt before generating.")
    else:
        with st.spinner("Generating presentation..."):
            ppt_path = generate_ppt(
                user_prompt=prompt
            )

        if not os.path.exists(ppt_path):
            st.error("PPT generation failed. File not found.")
        else:
            st.success("🎉 Presentation generated successfully!")

            with open(ppt_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PPT",
                    data=f,
                    file_name=os.path.basename(ppt_path),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
