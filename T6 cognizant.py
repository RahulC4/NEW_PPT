# =============================================
# generate_ppt_cognizant.py (FIXED)
# =============================================
import os
import uuid
from pptx import Presentation
from pptx.util import Pt
from utils import text_client, image_client, get_env, logger

TEMPLATE_PATH = "templates/Cognizant.pptx"


# --------------------------------------------------
# Rewrite content to Cognizant tone
# --------------------------------------------------
def rewrite_cognizant(title, bullets):
    bullets_text = "\n".join(f"- {b}" for b in bullets)

    prompt = f"""
Rewrite the following slide content in Cognizant enterprise style.

TITLE:
{title}

BULLETS:
{bullets_text}

Rules:
- Professional
- Clear
- Max 5 bullets
"""

    resp = text_client.chat.completions.create(
        model=get_env("CHAT_MODEL", required=True),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=300,
    )

    lines = resp.choices[0].message.content.split("\n")

    new_title = title
    new_bullets = []

    for l in lines:
        if l.lower().startswith("title"):
            new_title = l.split(":", 1)[1].strip()
        elif l.strip().startswith("-"):
            new_bullets.append(l[1:].strip())

    return new_title, new_bullets[:5]


# --------------------------------------------------
# MAIN GENERATOR
# --------------------------------------------------
def generate_presentation(payload):
    slides_data = payload.get("slides") or payload.get("preview_slides")
    if not slides_data:
        raise ValueError("No preview slides found")

    prs = Presentation(TEMPLATE_PATH)

    # Assume:
    # slide 0 = title
    # last slide = thank you
    content_template_slides = prs.slides[1:-1]

    # --------------------------------------------------
    # TITLE SLIDE
    # --------------------------------------------------
    title_slide = prs.slides[0]
    title_slide.shapes.title.text = slides_data[0]["title"]

    # --------------------------------------------------
    # CONTENT SLIDES
    # --------------------------------------------------
    data_slides = slides_data[1:]

    for i, data in enumerate(data_slides):
        title, bullets = rewrite_cognizant(
            data["title"],
            data.get("bullets", [])
        )

        # Reuse template slide if available
        if i < len(content_template_slides):
            slide = content_template_slides[i]
        else:
            slide = prs.slides.add_slide(prs.slide_layouts[1])

        # ---- Title ----
        if slide.shapes.title:
            slide.shapes.title.text = title

        # ---- Body ----
        for shape in slide.shapes:
            if shape.has_text_frame and shape != slide.shapes.title:
                tf = shape.text_frame
                tf.clear()
                for b in bullets:
                    p = tf.add_paragraph()
                    p.text = b
                    p.level = 0
                    p.font.size = Pt(18)
                break

        # ---- Image placeholders ----
        for shape in slide.shapes:
            if shape.shape_type == 13:  # picture placeholder
                prompt = f"Cognizant enterprise illustration for {title}"
                img = image_client.images.generate(
                    model=get_env("IMAGE_MODEL", required=True),
                    prompt=prompt,
                    size="1024x1024",
                )
                shape.insert_picture(img.data[0].b64_json)
                break

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    os.makedirs("generated", exist_ok=True)
    out = f"generated/cognizant_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out)
    return out
