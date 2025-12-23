def fill_content_body(slide, bullets):
    body = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 1:
            body = ph
            break

    if not body or not body.has_text_frame or not bullets:
        return

    tf = body.text_frame
    tf.clear()

    # ✅ FIRST BULLET — THIS IS THE KEY FIX
    tf.text = bullets[0]
    tf.paragraphs[0].level = 0
    tf.paragraphs[0].font.size = Pt(20)

    # ✅ REMAINING BULLETS
    for bullet in bullets[1:]:
        p = tf.add_paragraph()
        p.text = bullet
        p.level = 0
        p.font.size = Pt(20)
