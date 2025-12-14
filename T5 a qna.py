if st.button("Generate PPT"):
    st.session_state["generation_payload"] = {
        "selected_slides": selected_slides,
        "answers_map": st.session_state["answers_by_slide"]
    }
    st.switch_page("pages/4_Generate_PPT.py")
