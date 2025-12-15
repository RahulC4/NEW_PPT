def get_exact_slide_text(slide, max_chars=1200):
    """
    Fetch exact slide text using ppt_name + slide_index
    (NO embeddings, NO semantic search)
    """
    ppt_name = slide.get("ppt_name")
    slide_index = str(slide.get("slide_index"))

    if not ppt_name or slide_index is None:
        return ""

    try:
        res = collection.get(
            where={
                "ppt_name": ppt_name,
                "slide_index": slide_index
            }
        )
    except Exception:
        logger.exception("Chroma get() failed")
        return ""

    docs = res.get("documents", [])
    if not docs:
        return ""

    return "\n".join(docs)[:max_chars]





def chroma_questions(slide, max_q=3):
    """
    Generate questions from EXACT slide text (no semantic search)
    """
    context = get_exact_slide_text(slide)

    if not context:
        logger.warning(
            f"No exact text found in Chroma for "
            f"{slide.get('ppt_name')} | slide {slide.get('slide_index')}"
        )
        return []

    prompt = f"""
You are analysing a PowerPoint slide.

SLIDE CONTENT:
{context}

TASK:
Generate up to {max_q} diverse, non-overlapping questions
to help customize this slide.

Rules:
- Each question must focus on a DIFFERENT aspect
- Avoid objectives or key-points phrasing
- No generic questions
- Plain numbered list only
"""

    resp = text_client.chat.completions.create(
        model=get_env("CHAT_MODEL", required=True),
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=300
    )

    raw = resp.choices[0].message.content or ""
    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    questions = []
    for ln in lines:
        if ln[0].isdigit():
            q = ln.split(".", 1)[-1].strip()
            if q:
                questions.append(q)

    return questions[:max_q]
