# ============================================================
# generate_ppt_cognizant.py
# ============================================================
import os
import uuid
from pptx import Presentation
from pptx.util import Pt
from utils import logger


# ------------------------------------------------------------
# INTERNAL HELPERS
# ------------------------------------------------------------
def _delete_all_but_last_slide(prs):
    """
    Safely delete all slides except the LAST one.
    We assume the last slide is the Thank You slide
    coming from the Cognizant template.
    """
    slide_ids = list(prs.slides._sldIdLst)
    for slide_id in slide_ids[:-1]:
        prs.slides._sldIdLst.remove(slide_id)


def _clear_slide_text(slide):
    """
    Remove ALL text from a slide (placeholders + text boxes)
    """
    for shape in slide.shapes:
        if hasattr(shape, "text_frame"):
            shape.text_frame.clear()


def _set_title(slide, title_text):
    """
    Set title safely (works even if layout title placeholder missing)
    """
    if slide.shapes.title:
        slide.shapes.title.text = title_text
    else:
        txBox = slide.shapes.add_textbox(
            left=slide.part.slide_width * 0.1,
            top=slide.part.slide_height * 0.1,
            width=slide.part.slide_width * 0.8,
            height=Pt(60),
        )
        p = txBox.text_frame.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(28)
        p.font.bold = True


def _set_bullets(slide, bullets):
    """
    Put bullets into the first available body placeholder,
    or create one if not found.
    """
    body = None
    for shape in slide.shapes:
        if hasattr(shape, "text_frame") and shape != slide.shapes.title:
            body = shape.text_frame
            break

    if body is None:
        txBox = slide.shapes.add_textbox(
            left=slide.part.slide_width * 0.1,
            top
