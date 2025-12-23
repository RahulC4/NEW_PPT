# ============================================================
# generate_ppt_cognizant.py
# Cognizant Template | Preview-driven | TEXT-ONLY (No Images)
# ============================================================

import os
import uuid
import tempfile
from datetime import datetime
from pptx.dml.color import RGBColor
from pptx import Presentation
from pptx.util import Inches, Pt

from utils import logger


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
COGNIZANT_TEMPLATE = os.path.join(TEMPLATES_DIR, "Cognizant.pptx")


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def delete_slide(prs, index):
    slide_id = prs.slides._sldIdLst[index].rId
    prs.part.drop_rel(slide_id)
    del prs.slides._sldIdLst[index]


def remove_empty_placeholders(slide):
    """
    Removes 'Click to add...' textboxes
    """
    for shape in list(slide.shapes):
        if shape.has_text_frame:
            txt = shape.text_frame.text.strip().lower()
            if txt.startswith("click to add"):
                slide.shapes._spTree.remove(shape._element)


def update_month_year(slide):
    """
    Replaces any date-like text with current Month YYYY
    """
    current = datetime.now().strftime("%B %Y")
    for shape in slide.shapes:
        if shape.has_text_frame:
            if any(y in shape.text for y in ["2023", "2024", "2025"]):
                shape.text = current




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

    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(42)
    p.font.bold = True


def add_bullets(prs, slide, bullets):
    tb = slide.shapes.add_textbox(
        left=Inches(1),
        top=Inches(2),
        width=prs.slide_width - Inches(2),
        height=prs.slide_height - Inches(3),
    )

    tf = tb.text_frame
    tf.word_wrap = True
    tf.clear()

    for b in bullets:
        p = tf.add_paragraph()
        p.text = b
        p.font.size = Pt(20)
        p.level = 0


# ------------------------------------------------------------
# MAIN GENERATOR
# ------------------------------------------------------------
def generate_presentation_cognizant(payload):
    """
    Cognizant PPT generation
    - Preview driven
    - First & Last slide customized
    - No images
    """

    slides = payload.get("slides")
    if not slides:
        raise ValueError("No preview slides found")

    prs = Presentation(COGNIZANT_TEMPLATE)

    # Capture layouts BEFORE deleting slides
    title_layout = prs.slides[0].slide_layout
    content_layout = prs.slides[1].slide_layout
    thankyou_layout = prs.slides[-1].slide_layout

    # Delete all existing slides
    for i in reversed(range(len(prs.slides))):
        delete_slide(prs, i)

    # --------------------------------------------------------
    # 1️⃣ TITLE SLIDE
    # --------------------------------------------------------
    title_data = slides[0]

    title_slide = prs.slides.add_slide(title_layout)
    set_title_full_width(prs, title_slide, title_data.get("title", ""))
    update_month_year(title_slide)
    remove_empty_placeholders(title_slide)

    # --------------------------------------------------------
    # 2️⃣ CONTENT SLIDES
    # --------------------------------------------------------
    for slide_data in slides[1:]:
        slide = prs.slides.add_slide(content_layout)

        title = slide_data.get("title", "")
        bullets = [
            b.strip()
            for b in (slide_data.get("bullets") or [])
            if isinstance(b, str) and b.strip()
        ]

        # ✅ Title (template title placeholder)
        if slide.shapes.title:
            slide.shapes.title.text = title

        # ✅ BODY PLACEHOLDER (THIS IS THE KEY FIX)
        body = None
        for shape in slide.placeholders:
            if shape.is_placeholder and shape.placeholder_format.idx == 1:
                body = shape
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
                p.level = 0
                p.font.size = Pt(20)

        # ✅ Remove any leftover "Click to add text"
        remove_empty_placeholders(slide)

    # --------------------------------------------------------
    # 3️⃣ THANK YOU SLIDE (FIXED)
    # --------------------------------------------------------
    thank_slide = prs.slides.add_slide(thankyou_layout)

    # Force title text
    for shape in thank_slide.shapes:
        if shape.has_text_frame:
            shape.text = "Thank You"
            break

    remove_empty_placeholders(thank_slide)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------
    os.makedirs("generated", exist_ok=True)
    out_path = f"generated/cognizant_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out_path)
    return out_path
