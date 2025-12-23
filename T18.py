# --------------------------------------------------------
# 2️⃣ CONTENT SLIDES
# --------------------------------------------------------
for slide_data in slides[1:]:
    slide = clone_slide(prs, content_master)

    title = slide_data.get("title", "")
    bullets = [
        b.strip()
        for b in (slide_data.get("bullets") or [])
        if isinstance(b, str) and b.strip()
    ]

    # ---------- FIX 1: CONTENT TITLE (KEEP WHITE) ----------
    if slide.shapes.title:
        tf = slide.shapes.title.text_frame
        p = tf.paragraphs[0]          # ❗ DO NOT clear
        p.text = title
        p.font.color.rgb = RGBColor(255, 255, 255)  # ✅ force white
        p.font.bold = True

    # ---------- FIX 2: BODY PLACEHOLDER ONLY ----------
    body = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 1:
            body = ph
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
            p.level = 0              # ✅ THIS fixes first bullet
            p.font.size = Pt(20)

    # ---------- FIX 3: FOOTER (TEMPLATE-SAFE) ----------
    year = datetime.now().year
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text.strip().lower() == "footer":
            shape.text = f"© {year} Cognizant"
