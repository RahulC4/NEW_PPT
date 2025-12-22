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
            top=slide.part.slide_height * 0.25,
            width=slide.part.slide_width * 0.8,
            height=slide.part.slide_height * 0.6,
        )
        body = txBox.text_frame

    body.clear()

    for i, bullet in enumerate(bullets):
        p = body.add_paragraph() if i > 0 else body.paragraphs[0]
        p.text = bullet
        p.level = 0
        p.font.size = Pt(18)


# ============================================================
# MAIN GENERATOR — COGNIZANT THEME
# ============================================================
def generate_presentation_cognizant(payload):
    """
    Rules:
    - Preview slides are the ONLY source of truth
    - Cognizant template content is NEVER reused
    - Number of slides == number of preview slides + Thank You
    """

    preview_slides = payload.get("slides")
    if not preview_slides:
        raise ValueError("No preview slides found")

    template_path = os.path.join("templates", "Cognizant.pptx")
    if not os.path.exists(template_path):
        raise FileNotFoundError("Cognizant.pptx template not found")

    # --------------------------------------------------------
    # LOAD TEMPLATE
    # --------------------------------------------------------
    prs = Presentation(template_path)

    # --------------------------------------------------------
    # REMOVE ALL SAMPLE CONTENT (KEEP THANK YOU)
    # --------------------------------------------------------
    _delete_all_but_last_slide(prs)
    thank_you_slide = prs.slides[0]  # preserved

    # --------------------------------------------------------
    # CREATE SLIDES FROM PREVIEW (STRICT)
    # --------------------------------------------------------
    for slide_data in preview_slides:
        title = (slide_data.get("title") or "").strip()
        bullets = slide_data.get("bullets") or []

        # Normalize bullets
        bullets = [
            b.strip()
            for b in bullets
            if isinstance(b, str) and b.strip()
        ]

        # Use a standard content layout (layout index 1 works
        # consistently in Cognizant template)
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        _clear_slide_text(slide)

        _set_title(slide, title)

        if bullets:
            _set_bullets(slide, bullets)

    # --------------------------------------------------------
    # MOVE THANK YOU SLIDE TO END
    # --------------------------------------------------------
    prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])
    prs.slides._sldIdLst.append(prs.slides._sldIdLst[0])

    # --------------------------------------------------------
    # SAVE FILE
    # --------------------------------------------------------
    os.makedirs("generated", exist_ok=True)
    out_path = f"generated/cognizant_{uuid.uuid4().hex[:6]}.pptx"
    prs.save(out_path)

    return out_path
