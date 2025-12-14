import streamlit as st

from main_generator import generate_ppt
from storage.azure_blob_utils import (
    upload_source_ppt_to_blob,
    list_source_ppt_blobs,
)

st.set_page_config(page_title="AI PPT Generator", layout="wide")

st.title("AI PPT Generator")

# ============================================================
# UPLOAD TEMPLATE PPTs
# ============================================================
st.header("Template Dataset")

uploaded_ppt = st.file_uploader(
    "Upload a sample PPT template",
    type=["pptx"]
)

if uploaded_ppt:
    upload_source_ppt_to_blob(
        uploaded_ppt.read(),
        uploaded_ppt.name
    )
    st.success("Template uploaded successfully. Re-run ingestion to index it.")

templates = list_source_ppt_blobs()
if templates:
    st.write("Available templates:")
    st.write(templates)

st.divider()

# ============================================================
# GENERATION
# ============================================================
st.header("Generate Presentation")

prompt = st.text_input(
    "Enter your presentation request",
    placeholder="Create a proposal deck for CareSource client"
)

if prompt:
    st.subheader("Answer a few questions")

    title = st.text_input("Presentation Title")
    problem = st.text_area("Problem Statement")
    solution = st.text_area("Proposed Solution")
    team = st.text_area("Team Overview")
    contact = st.text_area("Contact Information")

    if st.button("Generate PPT"):
        with st.spinner("Generating presentation..."):
            ppt_path = generate_ppt(
                user_prompt=prompt,
                user_answers={
                    "title": title,
                    "problem": problem,
                    "solution": solution,
                    "team": team,
                    "contact": contact,
                }
            )

        st.success("Presentation generated!")
        with open(ppt_path, "rb") as f:
            st.download_button(
                "Download PPT",
                data=f,
                file_name=ppt_path.split("/")[-1]
            )
