# =============================================
# generate_ppt_cognizant.py
# =============================================
import os
import uuid
from pptx import Presentation
from pptx.util import Pt
from utils import text_client, image_client, get_env, logger

COGNIZANT_TEMPLATE_PATH = "templates/Cognizant.pptx"


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _rewrite_for_cognizant(title, bullets):
    """
    LLM rewrites preview content into Cognizant tone
    """
    bullets_text = "\n".join(f"- {b}" for b in bullets)

    prompt = f"""
You are a Cognizant consultant.

Rewrite the following slide content to match
Cognizant enterprise presentation standards.

TITLE:
{title}

BULLETS:
{bullets_text}

RULES:
- Professional
- Concise
- Business focused
- Max 5 bullets
"""

    resp = text_client.chat.completions.create(
        model=get_env("CHAT_MODEL", required=True),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4,
    )

    text = resp.choices[0].message.content.strip().split("\n")
    new_title = title
    new_bullets = []

    for line in text:
        if line.lower().startswith("title"):
            new_title = line.split(":", 1)[1].strip()
        elif line.startswith("-"):
            new_bullets.append(line[1:].strip())

    return new_title, new_bullets[:5]


def _generate_image(prompt):
    img = image_client.images.generate(
        model=get_env("IMAGE_MODEL", required=True),
        prompt=prompt,
        size="1024x1024",
    )
    return img.data[0].b64_json


# --------------------------------------------------
# MAIN GENERATOR
# --------------------------------------------------
def generate_presentation(payload):
    preview_slides = payload.get("slides") or payload.get("preview_slides")

    if not preview_slides:
        raise ValueError("No preview slides provided")

    prs = Presentation(COGNIZANT_TEMPLATE_PATH)

    # Keep last slide as Thank You
    THANK_YOU_SLIDE = prs.slides[-1]
    content_slides = prs.slides[:-1]

    # Remove all content slides except first (title)
    while len(prs.slides) > 2:
        r_id = prs.slides._sldIdLst[1].rId
        prs.part.drop_rel(r_id)
        del prs.slides._sldIdLst[1]

    # --------------------------------------------------
    # TITLE SLIDE
    # --------------------------------------------------
    title_slide = prs.slides[0]
    title_shape = title_slide.shapes.title
    title_shape.text = preview_slides[0]["title"]

    # --------------------------------------------------
    # CONTENT SLIDES
    # --------------------------------------------------
    for slide_data in preview_slides[1:]:
        title = slide_data["title"]
        bullets = slide_data.get("bullets", [])

        new_title, new_bullets = _rewrite_for_cognizant(title, bullets)

        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = new_title

        body = slide.placeholders[1].text_frame
        body.clear()

        for b in new_bullets:
            p = body.add_paragraph()
            p.text = b
            p.level = 0
            p.font.size = Pt(18)

        # IMAGE PLACEHOLDER (if exists)
        for shape in slide.shapes:
            if shape.shape_type == 13:  # picture placeholder
                img_prompt = f"Cognizant enterprise illustration for {new_title}"
                img_b64 = _generate_image(img_prompt)
                shape.insert_picture(img_b64)
                break

    # --------------------------------------------------
    # THANK YOU SLIDE (KEEP TEMPLATE)
    # --------------------------------------------------
    prs.slides.add_slide(THANK_YOU_SLIDE.slide_layout)

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    os.makedirs("generated", exist_ok=True)
    out = f"generated/cognizant_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out)
    return out
