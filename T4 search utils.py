out.append({
    "id": ids[i],
    "ppt_name": metas[i].get("ppt_name"),
    "slide_id": metas[i].get("slide_id"),
    "slide_index": int(metas[i].get("slide_index")),  # ✅ ADD THIS
    "title": metas[i].get("title"),
    "text": docs[i],
    "tags": metas[i].get("tags"),
    "score": dists[i]
})
