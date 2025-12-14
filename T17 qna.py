def generate_questions_for_slide(slide_struct):
    slide_title = slide_struct.get("title", "")
    slide_index = slide_struct.get("slide_index", "")

    query = f"Slide {slide_index}: {slide_title}".strip()
    if not query:
        raise ValueError("Missing slide title/index for Chroma query")

    # ---- Chroma Search ----
    results = semantic_search(query=query, top_k=3)

    if not results:
        raise RuntimeError(f"No indexed content found for slide: {query}")

    # 🔴 LIMIT CONTEXT SIZE (VERY IMPORTANT)
    retrieved_text = "\n".join(
        r.get("text", "")[:800] for r in results if r.get("text")
    ).strip()

    if not retrieved_text:
        raise RuntimeError("Chroma returned empty text")

    prompt = f"""
You are analysing a PowerPoint slide.

SLIDE TITLE:
{slide_title}

REFERENCE CONTENT:
{retrieved_text}

TASK:
Ask exactly 3–5 clear, practical questions that help
customize or refine THIS slide.

Rules:
- Questions must be specific to the content
- No generic questions
- Plain numbered text only
- Always return something

Start now.
"""

    for attempt in range(2):  # 👈 one retry
        resp = text_client.chat.completions.create(
            model=get_env("CHAT_MODEL", required=True),
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=300
        )

        raw = resp.choices[0].message.content
        if raw and raw.strip():
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            questions = []
            for ln in lines:
                if ln[0].isdigit():
                    q = ln.split(".", 1)[-1].strip()
                    if q:
                        questions.append(q)

            if questions:
                return questions

    # 🚨 HARD FAIL (no fallback)
    raise RuntimeError("LLM returned empty response after retry")
