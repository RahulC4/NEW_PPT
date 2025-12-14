def generate_questions_for_slide(slide_struct):
    editable_shapes = slide_struct.get("editable_shapes", [])
    if not editable_shapes:
        raise ValueError("No editable shapes found on slide")

    slide_text_dump = [
        {"shape_id": s["shape_id"], "text": s["text"]}
        for s in editable_shapes
        if s.get("text")
    ]

    if not slide_text_dump:
        raise ValueError("Slide text is empty")

    system_prompt = (
        "You are an expert presentation consultant.\n"
        "Analyze the slide content and generate slide-specific questions.\n\n"
        "STRICT RULES:\n"
        "- One question per shape_id\n"
        "- Questions must reference the slide text\n"
        "- NO generic questions\n"
        "- OUTPUT ONLY VALID JSON\n\n"
        "JSON FORMAT:\n"
        "{\n"
        '  "slide_title": "Improved slide title",\n'
        '  "questions": {\n'
        '    "shape_id": "question"\n'
        "  }\n"
        "}"
    )

    user_prompt = json.dumps(
        {"slide_content": slide_text_dump},
        indent=2
    )

    resp = text_client.chat.completions.create(
        model=get_env("CHAT_MODEL", required=True),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=600
    )

    raw = resp.choices[0].message.content

    # 🚨 CRITICAL GUARD
    if not raw or not raw.strip():
        raise RuntimeError("LLM returned empty response")

    # Try parsing JSON safely
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Invalid JSON from LLM.\nRaw output:\n{raw}"
        ) from e

    if "questions" not in parsed or not isinstance(parsed["questions"], dict):
        raise RuntimeError(
            f"Malformed JSON structure.\nParsed output:\n{parsed}"
        )

    return parsed
