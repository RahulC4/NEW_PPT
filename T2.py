with col2:
    if st.button("Next:Generate PPT"):
        st.session_state["generation_payload"] = {
            "slides": st.session_state["preview_slides"],
            "preview_only": True   # 🔒 HARD LOCK
        }
        st.switch_page("pages/5_Generate_PPT.py")



# 🔒 ENFORCE PREVIEW-ONLY GENERATION
if not payload.get("preview_only"):
    st.error("Invalid generation state. Please generate PPT from Preview page.")
    st.stop()
