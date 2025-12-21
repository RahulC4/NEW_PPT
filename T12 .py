import json
import hashlib

def _answers_signature(slides, answers_map):
    """
    Create a stable signature of slide selection + Q&A answers.
    If this changes, preview must be regenerated.
    """
    payload = []
    for s in slides:
        idx = str(s["slide_index"])
        payload.append({
            "slide_index": idx,
            "answers": answers_map.get(idx, {})
        })

    raw = json.dumps(payload, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


current_signature = _answers_signature(slides, answers_map)

# 🔥 INVALIDATE PREVIEW IF Q&A CHANGED
if st.session_state.get("_preview_signature") != current_signature:
    st.session_state.pop("preview_slides", None)
    st.session_state["_preview_signature"] = current_signature
