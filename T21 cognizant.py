# ============================================================
# generate_ppt_cognizant.py
# Cognizant Template | Preview-driven | TEXT-ONLY
# ============================================================

import os
import uuid
from datetime import datetime
from copy import deepcopy

from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

from utils import logger


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
COGNIZANT_TEMPLATE = os.path.join(TEMPLATES_DIR, "Cognizant.pptx")


# ------------------------------------------------------------
# SLIDE CLONE (DO NOT CHANGE)
# ------------------------------------------------------------
def clone_slide(prs, slide):
    new_slide = prs.slides.add_slide(slide.slide_layout)

    # Remove auto-added placeholders
    for shp in list(new_slide.shapes):
        new_slide.shapes._spTree.remove(shp._element)

    # Deep copy all shapes from master slide
    for shp in slide.shapes:
        new_slide.shapes._spTree.insert_element_before(
            deepcopy(shp._element), 'p:extLst'
        )

    return new_slide


# ------------------------------------------------------------
# FOOTER (ALL SLIDES)
# ------------------------------------------------------------
def update_footer(slide):
    year = datetime.now().year
    for ph in slide.placeholders:
        # FOOTER placeholder type
        if ph.placeholder_format.type == 10:
            ph.text = f"© {year} Cognizant"


# ------------------------------------------------------------
# TITLE SLIDE ONLY (WHITE + FULL WIDTH)
# ------------------------------------------------------------
def set_title_white_full_width(prs, slide, text):
    if not slide.shapes.title:
        return

    tf = slide.shapes.title.text_frame
    tf.clear()

    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)

    slide.shapes.title.left = Inches(0.5)
    slide.shapes.title.width = prs.slide_width - Inches(1)


# ------------------------------------------------------------
# CONTENT TITLE (KEEP TEMPLATE COLOR)
# ------------------------------------------------------------
def set_content_title(slide, title):
    if not slide.shapes.title:
        return

    tf = slide.shapes.title.text_frame
    p = tf.paragraphs[0]     # ❗ DO NOT clear (preserves white color)
    p.text = title


# ------------------------------------------------------------
# CONTENT BODY (CRITICAL FIX)
# ------------------------------------------------------------
def fill_content_body(slide, bullets):
    """
    Uses ONLY the existing body placeholder (right-side box).
    Fixes first bullet missing issue.
    Does NOT add any textbox.
    """

    body = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 1:  # BODY placeholder
            body = ph
            break

    if not body or not body.has_text_frame:
        logger.warning("Body placeholder not found on content slide")
        return

    tf = body.text_frame
    tf.clear()

    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        p.text = bullet
        p.level = 0              # ✅ FIRST POINT IS A BULLET
        p.font.size = Pt(20)


# ------------------------------------------------------------
# MAIN GENERATOR
# ------------------------------------------------------------
def generate_presentation_cognizant(payload):
    slides = payload.get("slides")
    if not slides:
        raise ValueError("No preview slides found")

    prs = Presentation(COGNIZANT_TEMPLATE)

    # Masters from template
    title_master = prs.slides[0]      # Title slide
    content_master = prs.slides[3]    # 4th slide = content design
    thankyou_master = prs.slides[-1]  # Thank You slide

    # Clear template slides
    for i in reversed(range(len(prs.slides))):
        slide_id = prs.slides._sldIdLst[i].rId
        prs.part.drop_rel(slide_id)
        del prs.slides._sldIdLst[i]

    # --------------------------------------------------------
    # TITLE SLIDE
    # --------------------------------------------------------
    title_slide = clone_slide(prs, title_master)
    set_title_white_full_width(prs, title_slide, slides[0].get("title", ""))
    update_footer(title_slide)

    # --------------------------------------------------------
    # CONTENT SLIDES
    # --------------------------------------------------------
    for slide_data in slides[1:]:
        slide = clone_slide(prs, content_master)

        set_content_title(slide, slide_data.get("title", ""))
        fill_content_body(slide, slide_data.get("bullets", []))
        update_footer(slide)

    # --------------------------------------------------------
    # THANK YOU SLIDE
    # --------------------------------------------------------
    thank_slide = clone_slide(prs, thankyou_master)
    if thank_slide.shapes.title:
        thank_slide.shapes.title.text = "Thank You"
    update_footer(thank_slide)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------
    os.makedirs("generated", exist_ok=True)
    out_path = f"generated/cognizant_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out_path)

    return out_path
