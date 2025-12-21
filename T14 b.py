# ---------------------------------------------------
# RESET PREVIEW WHEN PAYLOAD CHANGES
# ---------------------------------------------------
payload_signature = tuple(
    (s["slide_index"], s["slide_title"])
    for s in slides
)

if st.session_state.get("_preview_signature") != payload_signature:
    st.session_state["preview_slides"] = []
    st.session_state["_preview_signature"] = payload_signature

# ---------------------------------------------------
# INIT PREVIEW STATE (LLM CONTENT ONLY – ONCE PER PAYLOAD)
# ---------------------------------------------------
if not st.session_state["preview_slides"]:
