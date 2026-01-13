selected = []
slides_by_id = {s["slide_id"]: s for s in slides}

for slide_id in st.session_state["selected_slides"]:
    if slide_id in slides_by_id:
        selected.append(slides_by_id[slide_id])
