from pptx.dml.color import RGBColor

def set_title_full_width(prs, slide, text):
    """
    Wide title textbox to keep title in one line
    (FIRST SLIDE ONLY)
    """
    # Remove existing title placeholders
    for shape in list(slide.shapes):
        if shape.is_placeholder:
            slide.shapes._spTree.remove(shape._element)

    tb = slide.shapes.add_textbox(
        left=Inches(0.75),
        top=Inches(2.8),
        width=prs.slide_width - Inches(1.5),
        height=Pt(110),
    )

    tf = tb.text_frame
    tf.clear()

    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(48)                  # ⬆ increased from 42 → 48
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)  # ✅ WHITE
