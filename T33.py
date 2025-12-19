st.session_state["generation_payload"] = {
    "selected_slide_structs": st.session_state["selected_slide_structs"],
    "qna_answers": st.session_state.get("qna_answers", {}),
    "answers_by_slide": st.session_state.get("answers_by_slide", {})
}
