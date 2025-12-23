# ============================================================
# generate_ppt_cognizant.py
# Cognizant Template | Preview-driven | TEXT-ONLY
# Uses 4th slide as CONTENT MASTER (TRUE DESIGN CLONE)
# ============================================================

import os
import uuid
from datetime import datetime
from copy import deepcopy

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

from utils import logger


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
COGNIZANT_TEMPLATE = os.path.join(TEMPLATES_DIR, "Cognizant.pptx")


# ------------------------------------------------------------
# SLIDE CLONE (DESIGN SAFE)
# ------------------------------------------------------------
def clone_slide(prs, slide):
    new_slide = prs.slides.add_slide(slide.slide_layout)

    # remove auto placeholders
    for shp in list(new_slide.shapes):
        new_slide.shapes._spTree.remove(shp._element)

    # clone shapes
    for shp in slide.shapes:
        new_slide.shapes._spTree.insert_element_before(
            deepcopy(shp._element), 'p:extLst'
        )

    return new_slide


def update_footer(slide):
    year = datetime.now().year
    for shape in slide.placeholders:
        if shape.placeholder_format.type == 10:  # FOOTER
            shape.text = f"© {year} Cognizant"


def set_title_white(slide, text):
    if slide.shapes.title:
        tf = slide.shapes.title.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(48)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)


def fill_body_placeholder(slide, bullets):
    """
    Fills 'Click to add text' placeholder with bullets
    """
    body = None
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 1:  # BODY
            body = ph
            break

    if not body or not body.has_text_frame:
        return

    tf = body.text_frame
    tf.clear()

    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = bullet
        p.level = 0
        p.font.size = Pt(20)


# ------------------------------------------------------------
# MAIN GENERATOR
# ------------------------------------------------------------
def generate_presentation_cognizant(payload):
    slides = payload.get("slides")
    if not slides:
        raise ValueError("No preview slides found")

    prs = Presentation(COGNIZANT_TEMPLATE)

    # Capture master slides BEFORE delete
    title_master = prs.slides[0]
    content_master = prs.slides[3]   # 🔑 YOUR DESIGN SLIDE
    thankyou_master = prs.slides[-1]

    # delete all slides
    for i in reversed(range(len(prs.slides))):
        slide_id = prs.slides._sldIdLst[i].rId
        prs.part.drop_rel(slide_id)
        del prs.slides._sldIdLst[i]

    # --------------------------------------------------------
    # 1️⃣ TITLE SLIDE
    # --------------------------------------------------------
    title_slide = clone_slide(prs, title_master)
    set_title_white(title_slide, slides[0]["title"])
    update_footer(title_slide)

    # --------------------------------------------------------
    # 2️⃣ CONTENT SLIDES (USING 4TH SLIDE DESIGN)
    # --------------------------------------------------------
    for slide_data in slides[1:]:
        slide = clone_slide(prs, content_master)

        set_title_white(slide, slide_data.get("title", ""))
        fill_body_placeholder(slide, slide_data.get("bullets", []))
        update_footer(slide)

    # --------------------------------------------------------
    # 3️⃣ THANK YOU SLIDE
    # --------------------------------------------------------
    thank_slide = clone_slide(prs, thankyou_master)

    if thank_slide.shapes.title:
        thank_slide.shapes.title.text = "Thank You"

    update_footer(thank_slide)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------
    os.makedirs("generated", exist_ok=True)
    out = f"generated/cognizant_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out)
    return out
