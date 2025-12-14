# pages/1_Home.py
import os
import tempfile
import streamlit as st

from search_utils import semantic_search
from azure_blob_utils import download_source_ppt_from_blob
from slide_renderer import extract_slide_structure
from utils import logger

st.set_page_config(page_title="1 - Home", layout="wide")
st.title("1 — Home: Enter prompt and load reference slides")

# -------------------------------------------------
# Session initialization
# -------------------------------------------------
st.session_state.setdefault("slides_catalog", [])
st.session_state.setdefault("selected_slides", [])

prompt = st.text_area("Enter presentation prompt:", height=120)

if st.button("Search dataset & Load Slides"):
    if not prompt.strip():
        st.error("Please enter a prompt.")
        st.stop()

    with st.spinner("Searching dataset and loading relevant slides..."):

        st.session_state["slides_catalog"] = []
        st.session_state["selected_slides"] = []

        # 🔑 Slide-level semantic results
        refs = semantic_search(prompt, top_k=12)

        if not refs:
            st.warning("No relevant slides found.")
            st.stop()

        for r in refs:
            try:
                ppt_blob = r.get("ppt_name")
                slide_id = r.get("slide_id")  # <-- THIS EXISTS

                if not ppt_blob or not slide_id:
                    continue

                # ✅ Extract slide index from slide_id
                # Example: Carefirst.pptx_Slide_03 → 3
                slide_index = int(slide_id.split("_Slide_")[-1])

                local_ppt = os.path.join(
                    tempfile.gettempdir(),
                    ppt_blob.replace("/", "_")
                )

                if not os.path.exists(local_ppt):
                    download_source_ppt_from_blob(ppt_blob, local_ppt)

                slide_struct = extract_slide_structure(local_ppt, slide_index)
                slide_struct["ppt_blob"] = ppt_blob
                slide_struct["slide_id"] = slide_id

                st.session_state["slides_catalog"].append(slide_struct)

                if len(st.session_state["slides_catalog"]) >= 12:
                    break

            except Exception as e:
                logger.exception(f"Failed loading slide: {e}")

        if st.session_state["slides_catalog"]:
            st.success(
                f"Loaded {len(st.session_state['slides_catalog'])} relevant reference slides"
            )
            st.switch_page("pages/2_🖼️_Slide_Selection.py")
        else:
            st.warning("No slides could be loaded.")
