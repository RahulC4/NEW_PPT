def get_exact_slide_text(slide, max_chars=1200):
    """
    Fetch exact slide text from Chroma using slide_id + slide_index
    """
    slide_id = slide.get("slide_id")
    slide_index = str(slide.get("slide_index"))

    if not slide_id:
        return ""

    try:
        res = collection.get(
            where={
                "slide_id": slide_id,
                "slide_index": slide_index
            }
        )
    except Exception:
        logger.exception("Exact Chroma get() failed")
        return ""

    docs = res.get("documents", [])
    if not docs:
        return ""

    return "\n".join(docs)[:max_chars]


context = get_exact_slide_text(slide)
if not context:
    return []



def chroma_questions(slide, max_q=3):
    """
    Generate up to max_q questions using EXACT slide text
    (no semantic search, no slide_index)
    """

    # 🔹 Get exact slide text from Chroma
    context = get_exact_slide_text(slide)

    if not context:
        logger.warning(
            f"No exact text found in Chroma for slide_id={slide.get('slide_id')}"
        )
        return []

    prompt = f"""
You are analysing the following PowerPoint slide content.

SLIDE CONTENT:
{context}

TASK:
Generate up to {max_q} diverse, non-overlapping questions
to help customize this slide.

Rules:
- Each question must focus on a DIFFERENT aspect
  (e.g., scope, metrics, assumptions, risks, outcomes)
- Avoid repeating objectives or key points
- No generic questions
- Plain numbered text only
- One question per line
"""

    try:
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

    except Exception as e:
        logger.exception("LLM failed while generating questions from exact slide text")
        return []




def get_exact_slide_text(slide, max_chars=1200):
    slide_id = slide.get("slide_id")
    if not slide_id:
        return ""

    try:
        res = collection.query(
            query_texts=[""],               # dummy query
            n_results=1,
            where={"slide_id": slide_id}
        )
    except Exception:
        logger.exception("Exact slide query failed")
        return ""

    docs = res.get("documents", [[]])[0]
    if not docs:
        return ""

    return docs[0][:max_chars]
