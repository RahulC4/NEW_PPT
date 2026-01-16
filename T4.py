with col2:
    if st.button("Next:Generate PPT"):
        # 🔑 REBUILD payload from edited preview slides
        st.session_state["generation_payload"] = {
            "slides": st.session_state["preview_slides"],   # edited content
            "answers_map": payload.get("answers_map", {})   # keep answers
        }

        st.switch_page("pages/5_Generate_PPT.py")
