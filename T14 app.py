# frontend/app.py

import os
import sys
import tempfile
import streamlit as st
from pptx import Presentation

# ======================================================
# 🔑 CRITICAL FIX: add PROJECT ROOT to PYTHONPATH
# ======================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ======================================================
# Backend imports (NOW WILL WORK)
# ======================================================
from backend.search_utils import semantic_search, collection
from backend.azure_blob_utils import download_source_ppt_from_blob
from backend.slide_renderer import extract_slide_structure
from backend.utils import logger

# ======================================================
# Streamlit config
# ======================================================
st.set_page_config(page_title="AI PPT Generator", layout="wide")
st.title("Step 1 — Start Your Presentation")

# ======================================================
# Session init
# ======================================================
st.session_state.setdefault("slides_catalog", [])
st.session_state.setdefault("selected_slides", [])
st.session_state.setdefault("ppt_theme", "auto")

# ======================================================
# Helper
# ======================================================
def get_slide_title_from_chroma(ppt_name, slide_index):
    try:
        res = collection.get(
            where={
                "$and": [
                    {"ppt_name": ppt_name},
                    {"slide_index": slide_index}
                ]
            }
        )
        metas = res.get("metadatas", [])
        if metas and metas[0].get("title"):
            return metas[0]["title"].strip()
    except Exception:
        logger.exception("Chroma title fetch failed")
    return None

# ======================================================
# UI
# ======================================================
prompt = st.text_area("Enter presentation prompt:", height=120)

theme = st.selectbox("Select Presentation Theme", ["auto", "cognizant"])
st.session_state["ppt_theme"] = theme

# ======================================================
# Action
# ======================================================
if st.button("Search dataset & Load Slides"):
    if not prompt.strip():
        st.error("Please enter a prompt.")
        st.stop()

    with st.spinner("Searching dataset..."):
        st.session_state["slides_catalog"] = []
        st.session_state["selected_slides"] = []

        refs = semantic_search(prompt, top_k=12)

        if not refs:
            st.warning("No relevant slides found.")
            st.stop()

        for r in refs:
            ppt_blob = r["ppt_name"]
            slide_index = r["slide_index"]

            local_ppt = os.path.join(
                tempfile.gettempdir(),
                ppt_blob.replace("/", "_")
            )

            if not os.path.exists(local_ppt):
                download_source_ppt_from_blob(ppt_blob, local_ppt)

            slide_struct = extract_slide_structure(local_ppt, slide_index)
            slide_struct["ppt_blob"] = ppt_blob
            slide_struct["slide_id"] = r["slide_id"]

            st.session_state["slides_catalog"].append(slide_struct)

        st.success(f"Loaded {len(st.session_state['slides_catalog'])} slides")
        st.switch_page("frontend/pages/2_🖼️_Slide_Selection.py")
