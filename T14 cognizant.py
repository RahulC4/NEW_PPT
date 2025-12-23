# ============================================================
# generate_ppt_cognizant.py
# Cognizant Template | Preview-driven | TEXT-ONLY
# Uses 4th slide as CONTENT MASTER (REAL DESIGN COPY)
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
# LOW-LEVEL SLIDE CLONE (THIS IS THE MAGIC)
# ------------------------------------------------------------
def clone_slide(prs, slide):
    """
    Deep clone a slide INCLUDING design, shapes, background
    """
    slide_layout = slide.slide_layout
    new_slide = prs.slides.add_slide(slide_layout)

    # Remove auto-added placeholders
    for shp in list(new_slide.shapes):
        new_slide.shapes._spTree.remove(shp._element)

    # Copy shapes XML
    for shp in slide.shapes:
        new_slide.shapes._spTree.insert_element_before(
            deepcopy(shp._element), 'p:extLst'
        )

    return new_slide


def remove_click_to_add(slide):
    for shape in list(slide.shapes):
        if shape.has_text_frame:
            txt = shape.text_frame.text.lower().strip()
            if txt.startswith("click to add"):
                slide.shapes._spTree.remove(shape._element)


def update_month_year(slide):
    current = datetime.now().strftime("%B %Y")
    for shape in slide.shapes:
        if shape.has_text_frame:
            if any(y in shape.text for y in ["2023", "2024", "2025"]):
                shape.text = current


def set_first_slide_title(prs, slide, text):
    for shape in list(slide.shapes):
        if shape.is_placeholder:
            slide.shapes._spTree.remove(shape._element)

    tb = slide.shapes.add_textbox(
        prs.slide_width * 0.05,
        prs.slide_height * 0.35,
        prs.slide_width * 0.9,
        Pt(110),
    )

    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)


# ------------------------------------------------------------
# MAIN GENERATOR
# ------------------------------------------------------------
def generate_presentation_cognizant(payload):
    slides = payload.get("slides")
    if not slides:
        raise ValueError("No preview slides found")

    prs = Presentation(COGNIZANT_TEMPLATE)

    # 🔥 Capture MASTER slides BEFORE deletion
    title_master = prs.slides[0]
    content_master = prs.slides[3]     # 👈 YOUR SAMPLE SLIDE
    thankyou_master = prs.slides[-1]

    # Delete everything
    for i in reversed(range(len(prs.slides))):
        slide_id = prs.slides._sldIdLst[i].rId
        prs.part.drop_rel(slide_id)
        del prs.slides._sldIdLst[i]

    # --------------------------------------------------------
    # 1️⃣ TITLE SLIDE
    # --------------------------------------------------------
    title_slide = clone_slide(prs, title_master)
    set_first_slide_title(prs, title_slide, slides[0]["title"])
    update_month_year(title_slide)
    remove_click_to_add(title_slide)

    # --------------------------------------------------------
    # 2️⃣ CONTENT SLIDES (TRUE DESIGN COPY)
    # --------------------------------------------------------
    for slide_data in slides[1:]:
        slide = clone_slide(prs, content_master)

        title = slide_data.get("title", "")
        bullets = slide_data.get("bullets", [])

        # Replace title
        if slide.shapes.title:
            slide.shapes.title.text = title

        # Replace body
        for shape in slide.shapes:
            if shape.has_text_frame and shape != slide.shapes.title:
                tf = shape.text_frame
                tf.clear()

                for i, b in enumerate(bullets):
                    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    p.text = b
                    p.level = 0
                    p.font.size = Pt(20)
                break

        remove_click_to_add(slide)

    # --------------------------------------------------------
    # 3️⃣ THANK YOU SLIDE
    # --------------------------------------------------------
    thank_slide = clone_slide(prs, thankyou_master)
    for shape in thank_slide.shapes:
        if shape.has_text_frame:
            shape.text = "Thank You"
            break

    remove_click_to_add(thank_slide)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------
    os.makedirs("generated", exist_ok=True)
    out = f"generated/cognizant_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out)
    return out
