layout_meta = extract_slide_layout_metadata(prs, i)

metadata.update({
    "layout_name": layout_meta["layout_name"],
    "master_name": layout_meta["master_name"],
    "placeholders": layout_meta["placeholders"]
})
