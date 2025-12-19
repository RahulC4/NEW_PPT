for slide in slides:
    slide_idx = str(slide["slide_index"])
    slide_title = slide["slide_title"]
    user_answers = answers_map.get(slide_idx, {})

    # -----------------------------------------------------------
    # CASE 1 — PRESENTATION TITLE SLIDE (ONLY FIRST SLIDE)
    # -----------------------------------------------------------
    if "What should be the title of this presentation?" in user_answers:
        title_text = user_answers[
            "What should be the title of this presentation?"
        ].strip()

        subtitle = None
        for v in user_answers.values():
            if "202" in v:
                subtitle = v.strip()
                break

        add_title_slide(prs, title_text, subtitle)
        continue   # 🚨 VERY IMPORTANT

    # -----------------------------------------------------------
    # FROM HERE ON → ALL NON-TITLE SLIDES
    # -----------------------------------------------------------
    ppt_slide = prs.slides.add_slide(prs.slide_layouts[1])

    # -----------------------------------------------------------
    # CASE 2 — USER SKIPPED ANSWERS
    # -----------------------------------------------------------
    valid_answers_exist = any(v.strip() for v in user_answers.values())
    if not valid_answers_exist:
        ppt_slide.shapes.title.text = slide_title
        continue

    # -----------------------------------------------------------
    # CASE 3 — NORMAL CONTENT GENERATION
    # -----------------------------------------------------------
    try:
        llm_title, bullets = llm_synthesize_slide(
            user_answers,
            global_prompt
        )
    except Exception:
        logger.exception("LLM failed")
        bullets = ["Content could not be generated"]

    ppt_slide.shapes.title.text = slide_title
    body = ppt_slide.placeholders[1].text_frame
    body.clear()

    for b in bullets:
        para = body.add_paragraph()
        para.text = b
        para.level = 0
        para.font.size = Pt(18)
