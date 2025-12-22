# --------------------------------------------------------
# 2️⃣ CONTENT SLIDES (FINAL FIX)
# --------------------------------------------------------
for slide_data in slides[1:]:
    slide = prs.slides.add_slide(content_layout)

    title = slide_data.get("title", "")
    bullets = [
        b.strip()
        for b in (slide_data.get("bullets") or [])
        if isinstance(b, str) and b.strip()
    ]

    # ✅ Title (template title placeholder)
    if slide.shapes.title:
        slide.shapes.title.text = title

    # ✅ BODY PLACEHOLDER (THIS IS THE KEY FIX)
    body = None
    for shape in slide.placeholders:
        if shape.is_placeholder and shape.placeholder_format.idx == 1:
            body = shape
            break

    if body and body.has_text_frame:
        tf = body.text_frame
        tf.clear()

        for i, bullet in enumerate(bullets):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()

            p.text = bullet
            p.level = 0
            p.font.size = Pt(20)

    # ✅ Remove any leftover "Click to add text"
    remove_empty_placeholders(slide)
