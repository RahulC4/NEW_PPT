import os
import streamlit as st
from datetime import datetime
from utils import logger

st.set_page_config(page_title="5 - Generate PPT", layout="wide")
st.title("Step 5 — Generate Your Presentation")

# ------------------------------------------------------------
# SAFE SESSION INIT
# ------------------------------------------------------------
if "generated_ppts" not in st.session_state:
    st.session_state["generated_ppts"] = []

if "ppt_generated_once" not in st.session_state:
    st.session_state["ppt_generated_once"] = False

payload = st.session_state.get("generation_payload")
theme = st.session_state.get("ppt_theme", "auto")

if not payload:
    st.warning("No generation payload found. Complete preview first.")
    st.stop()

# ------------------------------------------------------------
# AUTO GENERATE (ONCE)
# ------------------------------------------------------------
if not st.session_state["ppt_generated_once"]:
    try:
        with st.spinner("Generating final PPT..."):

            # ---------------- GENERATE ----------------
            if theme == "cognizant":
                from generate_ppt_cognizant import generate_presentation_cognizant
                out_path = generate_presentation_cognizant(payload)
            else:
                from generate_ppt_llm import generate_presentation
                out_path = generate_presentation(payload)

            # ---------------- TITLE FROM PREVIEW ----------------
            ppt_title = (
                payload.get("slides", [{}])[0].get("title")
                or "Generated_Presentation"
            )

            safe_title = "".join(
                c for c in ppt_title if c.isalnum() or c in (" ", "_", "-")
            ).strip().replace(" ", "_")

            timestamp = datetime.now().strftime("%d_%b_%H-%M")
            display_name = f"{safe_title}_{timestamp}.pptx"

            # ---------------- STORE IN SESSION ----------------
            st.session_state["generated_ppts"].insert(
                0,
                {
                    "path": out_path,
                    "name": display_name,
                    "created_at": datetime.now(),
                }
            )

            st.session_state["ppt_generated_once"] = True

        st.success("✅ PPT generated successfully!")

    except Exception as e:
        logger.exception("PPT generation failed")
        st.error(f"Failed to generate PPT: {e}")
        st.stop()

# ------------------------------------------------------------
# SHOW GENERATED PPTs
# ------------------------------------------------------------
st.markdown("---")
st.subheader("📂 Generated PPTs (This Session)")

if not st.session_state["generated_ppts"]:
    st.caption("No PPTs generated yet.")
else:
    for idx, item in enumerate(st.session_state["generated_ppts"]):
        col1, col2 = st.columns([4, 2])

        with col1:
            st.write(f"{idx + 1}. {item['name']}")

        with col2:
            try:
                with open(item["path"], "rb") as f:
                    st.download_button(
                        "⬇️ Download",
                        data=f,
                        file_name=item["name"],
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        key=f"download_{idx}",
                    )
            except Exception:
                st.caption("File not available")

# ------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------
if st.button("⬅ Back to Home"):
    st.switch_page("pages/1_Home.py")
