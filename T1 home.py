# pages/1_Home.py
import os
import tempfile
import streamlit as st
from pptx import Presentation

from search_utils import semantic_search
from azure_blob_utils import download_source_ppt_from_blob
from slide_renderer import extract_slide_structure
from utils import logger

st.set_page_config(page_title="1 - Home", layout="wide")
st.title("1 — Home: Enter prompt and load reference slides")

# -----------------------
# Session init
# -----------------------
st.session_state.setdefault("slides_catalog", [])
st.session_state.setdefault("selected_slides", [])

prompt = st.text_area("Enter presentation prompt:", height=120)

if st.button("Search dataset & Load Slides"):
    if not prompt.strip():
        st.error("Please enter a prompt.")
    else:
        with st.spinner("Searching dataset and loading slides..."):
            st.session_state["slides_catalog"] = []
            st.session_state["selected_slides"] = []

            refs = semantic_search(prompt, top_k=12)
            if not refs:
                st.warning("No relevant slides found.")
            else:
                ppt_names = list(dict.fromkeys(
                    r["ppt_name"] for r in refs if r.get("ppt_name")
                ))

                for ppt_blob in ppt_names:
                    try:
                        local_ppt = os.path.join(
                            tempfile.gettempdir(),
                            ppt_blob.replace("/", "_")
                        )
                        download_source_ppt_from_blob(ppt_blob, local_ppt)

                        prs = Presentation(local_ppt)
                        for idx in range(len(prs.slides)):
                            slide_struct = extract_slide_structure(local_ppt, idx)
                            slide_struct["ppt_blob"] = ppt_blob
                            slide_struct["slide_id"] = f"{ppt_blob}_slide_{idx}"
                            st.session_state["slides_catalog"].append(slide_struct)

                            if len(st.session_state["slides_catalog"]) >= 12:
                                break
                    except Exception as e:
                        logger.exception(f"Failed loading {ppt_blob}: {e}")

                if st.session_state["slides_catalog"]:
                    st.success(
                        f"Loaded {len(st.session_state['slides_catalog'])} reference slides"
                    )
                    st.switch_page("pages/2_🖼️_Slide_Selection.py")
