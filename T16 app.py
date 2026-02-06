# frontend/app.py
import sys
import os
import streamlit as st

# 🔑 ADD PROJECT ROOT TO PYTHON PATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

st.set_page_config(page_title="AI PPT Generator", layout="wide")

# Redirect to Home
st.switch_page("pages/1_Home.py")
