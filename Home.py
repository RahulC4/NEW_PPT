# pages/1_Home.py
import os
import tempfile
import streamlit as st
from pptx import Presentation
from search_utils import semantic_search
from azure_blob_utils import download_source_ppt_from_blob
from slide_extractor import extract_slides_info_from_ppt
from utils import logger

st.set_page_config(page_title="1 - Home", layout="wide")
st.title("1 — Home: Enter prompt and load reference slides")

if "slides_catalog" not in st.session_state:
    st.session_state["slides_catalog"] = []

prompt = st.text_area("Enter presentation prompt:", height=120)

if st.button("Search dataset & Load Slides"):
    if not prompt.strip():
        st.error("Please enter a prompt.")
    else:
        with st.spinner("Searching dataset..."):
            refs = semantic_search(prompt, top_k=12)
            if not refs:
                st.warning("No relevant slides found.")
            else:
                st.session_state["slides_catalog"] = []
                ppt_names = list(dict.fromkeys(r["ppt_name"] for r in refs))

                for ppt_blob in ppt_names:
                    try:
                        local = os.path.join(tempfile.gettempdir(), ppt_blob.replace("/", "_"))
                        download_source_ppt_from_blob(ppt_blob, local)
                        slides = extract_slides_info_from_ppt(local)
                        st.session_state["slides_catalog"].extend(slides)
                    except Exception as e:
                        logger.exception(e)

                st.success(f"Loaded {len(st.session_state['slides_catalog'])} reference slides")
                st.switch_page("pages/2_🖼️_Slide_Selection.py")
