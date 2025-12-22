# --------------------------------------------------------
# 2️⃣ CONTENT SLIDES (FIXED)
# --------------------------------------------------------
for slide_data in slides[1:]:
    slide = prs.slides.add_slide(content_layout)

    title = slide_data.get("title", "")
    bullets = [
        b.strip()
        for b in (slide_data.get("bullets") or [])
        if isinstance(b, str) and b.strip()
    ]

    # ✅ Set title (template title placeholder)
    if slide.shapes.title:
        slide.shapes.title.text = title

    # ✅ REMOVE template body placeholders ("Click to add text")
    remove_empty_placeholders(slide)

    # ✅ ADD bullets in our own textbox
    if bullets:
        add_bullets(prs, slide, bullets)
