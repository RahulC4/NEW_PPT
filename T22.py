def fill_content_body(slide, bullets):
    body = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 1:
            body = ph
            break

    if not body or not body.has_text_frame:
        return

    tf = body.text_frame
    tf.clear()

    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        p.text = bullet
        p.level = 0                 # ✅ THIS IS ENOUGH
        p.font.size = Pt(20)
