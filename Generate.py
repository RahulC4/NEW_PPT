# generate_ppt.py
import os
import uuid
from pptx import Presentation
from pptx.util import Pt
from utils import logger

def add_title_slide(prs, title):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = "Prepared by AI PPT Generator"

def add_agenda(prs, titles):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Agenda"
    body = slide.placeholders[1].text_frame
    body.clear()
    for t in titles:
        body.add_paragraph().text = t

def add_content_slide(prs, title, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title
    tf = slide.placeholders[1].text_frame
    tf.clear()
    for b in bullets:
        tf.add_paragraph().text = b

def add_thankyou(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Thank You"

def generate_presentation(payload):
    prs = Presentation()
    slide_titles = []

    for data in payload.values():
        slide_titles.append(data["title"])

    add_title_slide(prs, "Client Proposal")
    add_agenda(prs, slide_titles)

    for data in payload.values():
        bullets = [v for v in data["answers"].values() if v.strip()]
        add_content_slide(prs, data["title"], bullets)

    add_thankyou(prs)

    out = os.path.join("generated", f"ppt_{uuid.uuid4().hex[:6]}.pptx")
    os.makedirs("generated", exist_ok=True)
    prs.save(out)
    logger.info(f"Generated PPT: {out}")
    return out
