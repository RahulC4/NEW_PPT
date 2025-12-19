def add_title_slide(prs, title_text, subtitle_text=None):
    """
    Creates a clean title slide:
    - Large centered title
    - Optional subtitle/date
    - No bullets
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank slide

    # Title
    title_box = slide.shapes.add_textbox(
        left=prs.slide_width * 0.15,
        top=prs.slide_height * 0.35,
        width=prs.slide_width * 0.7,
        height=Pt(80),
    )

    tf = title_box.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(40)
    p.font.bold = True
    p.alignment = 1  # CENTER

    # Optional subtitle (date / context)
    if subtitle_text:
        sub_box = slide.shapes.add_textbox(
            left=prs.slide_width * 0.15,
            top=prs.slide_height * 0.48,
            width=prs.slide_width * 0.7,
            height=Pt(40),
        )
        tf2 = sub_box.text_frame
        tf2.clear()
        sp = tf2.paragraphs[0]
        sp.text = subtitle_text
        sp.font.size = Pt(18)
        sp.alignment = 1  # CENTER


is_title_slide = "What should be the title of this presentation?" in user_answers

# -----------------------------------------------------------
# CASE 1 — PRESENTATION TITLE SLIDE (ONLY FIRST SLIDE)
# -----------------------------------------------------------
if is_title_slide:
    title_text = user_answers[
        "What should be the title of this presentation?"
    ].strip()

    subtitle = None
    for v in user_answers.values():
        if "202" in v:  # crude but effective date detection
            subtitle = v.strip()
            break

    add_title_slide(prs, title_text, subtitle)
    continue
