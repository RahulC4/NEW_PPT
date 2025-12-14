# streamlit_app.py

import streamlit as st
import json
from main_generator import PresentationGenerator, create_presentation_pipeline
from storage.azure_blob_utils import (
    upload_source_ppt_to_blob,
    list_source_ppt_blobs,
    list_generated_presentations,
)
from ingestion.ingestion_chroma import process_blob
from utils import logger


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI PPT Generator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI PowerPoint Generator")
st.write("Generate **enterprise-grade PPT decks** using your sample templates and Azure OpenAI.")


# ============================================================
# SIDEBAR — PPT Dataset Upload
# ============================================================
st.sidebar.header("📁 Template Dataset")

uploaded_ppt = st.sidebar.file_uploader(
    "Upload Sample PPT Templates (for semantic ingestion)",
    type=["pptx"],
    accept_multiple_files=False
)

if uploaded_ppt:
    blob_key = upload_source_ppt_to_blob(
        uploaded_ppt.read(),
        uploaded_ppt.name
    )
    st.sidebar.success(f"Uploaded: {blob_key}")

    # Trigger ingestion for this PPT
    process_blob(uploaded_ppt.name)
    st.sidebar.success("PPT ingested into Chroma successfully.")

# Show existing templates
st.sidebar.subheader("Your Template Library")
ppt_list = list_source_ppt_blobs()
if ppt_list:
    st.sidebar.write("Available sample decks:")
    st.sidebar.write("\n".join(ppt_list))
else:
    st.sidebar.info("No sample templates found yet.")


# ============================================================
# MAIN WORKFLOW
# ============================================================
st.subheader("1️⃣ Enter Your Presentation Request")

user_prompt = st.text_area(
    "Describe the presentation you want to generate:",
    height=120,
    placeholder="Example: Create a proposal deck for CareSource client..."
)

engine = PresentationGenerator()


# ============================================================
# STEP 1: PRESENTATION PLANNING
# ============================================================
if st.button("Generate Slide Plan"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        with st.spinner("Creating slide plan..."):
            plan = engine.plan_from_prompt(user_prompt)
        st.session_state["plan"] = plan
        st.success("Slide plan created!")

        st.json(plan)


# ============================================================
# STEP 2: Q&A GENERATION
# ============================================================
if "plan" in st.session_state:
    st.subheader("2️⃣ Answer These Questions")

    plan = st.session_state["plan"]
    questions = engine.get_questions(plan)
    st.session_state["questions"] = questions

    if "answers" not in st.session_state:
        st.session_state["answers"] = {}

    answers = st.session_state["answers"]

    q_form = st.form("qna_form")
    for q in questions["questions"]:
        field = q["field"]
        question_txt = q["question"]

        answers[field] = q_form.text_input(
            question_txt,
            value=answers.get(field, "")
        )

    submitted = q_form.form_submit_button("Submit Answers")

    if submitted:
        st.session_state["answers"] = answers
        st.success("Answers saved!")


# ============================================================
# STEP 3: TEMPLATE MAPPING + PPT GENERATION
# ============================================================
if "answers" in st.session_state and "plan" in st.session_state:
    st.subheader("3️⃣ Generate Final PowerPoint")

    if st.button("Generate PPT"):
        with st.spinner("Mapping templates & generating PPT..."):
            plan = st.session_state["plan"]
            answers = st.session_state["answers"]

            mapped = engine.map_templates(plan)
            profile = engine.build_profile(plan, answers)

            tmp_ppt_path = engine.generate_ppt(mapped, profile)
            blob_path = engine.upload_output(tmp_ppt_path)

        st.session_state["ppt_blob"] = blob_path
        st.success("PPT successfully generated!")

        st.write(f"🎉 PPT uploaded to Azure Blob:")
        st.code(blob_path)


# ============================================================
# STEP 4: DOWNLOAD GENERATED PPTS
# ============================================================
st.subheader("📥 Download Previous Generated PPTs")

generated_list = list_generated_presentations()
if generated_list:
    st.selectbox("Generated Files:", generated_list)
else:
    st.info("No generated PPTs available yet.")
