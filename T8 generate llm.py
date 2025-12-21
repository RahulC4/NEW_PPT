def generate_presentation(payload):
    preview = payload.get("preview_slides", [])
    if not preview:
        raise ValueError("No preview slides provided")

    prs = Presentation()

    for slide in preview:
        # Title slide
        if slide["type"] == "title":
            add_title_slide(prs, slide["title"])
            continue

        ppt_slide = prs.slides.add_slide(prs.slide_layouts[1])
        ppt_slide.shapes.title.text = slide["title"]

        body = ppt_slide.placeholders[1].text_frame
        body.clear()

        for b in slide.get("bullets", []):
            p = body.add_paragraph()
            p.text = b
            p.level = 0
            p.font.size = Pt(18)

    # Thank you slide
    thanks = prs.slides.add_slide(prs.slide_layouts[1])
    thanks.shapes.title.text = "Thank You"

    os.makedirs("generated", exist_ok=True)
    out_path = f"generated/ppt_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out_path)
    return out_path
