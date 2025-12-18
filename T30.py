payload = st.session_state.get("generation_payload", {}).copy()

# ---- FIX: normalize payload for generate_ppt.py ----
payload["selected_slide_structs"] = (
    payload.get("selected_slide_structs")
    or st.session_state.get("selected_slide_structs")
    or []
)

payload["qna_answers"] = (
    payload.get("qna_answers")
    or st.session_state.get("qna_answers")
    or {}
)

payload["answers_by_slide"] = (
    payload.get("answers_by_slide")
    or st.session_state.get("answers_by_slide")
    or {}
)
