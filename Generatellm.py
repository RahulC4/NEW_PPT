# =============================================
# generate_ppt_llm.py
# =============================================
import os
import uuid
from pptx import Presentation
from pptx.util import Pt
from utils import text_client, get_env, logger


def add_title_slide(prs, title_text, subtitle_text=None):
    """
    Creates a clean title slide:
    - Large centered title
    - Optional subtitle/date
    - No bullets
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank slide

    # Title
    title_box = slide.shapes.add_textbox(
        left=prs.slide_width * 0.15,
        top=prs.slide_height * 0.35,
        width=prs.slide_width * 0.7,
        height=Pt(80),
    )

    tf = title_box.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(40)
    p.font.bold = True
    p.alignment = 1  # CENTER

    # Optional subtitle (date / context)
    if subtitle_text:
        sub_box = slide.shapes.add_textbox(
            left=prs.slide_width * 0.15,
            top=prs.slide_height * 0.48,
            width=prs.slide_width * 0.7,
            height=Pt(40),
        )
        tf2 = sub_box.text_frame
        tf2.clear()
        sp = tf2.paragraphs[0]
        sp.text = subtitle_text
        sp.font.size = Pt(18)
        sp.alignment = 1  # CENTER
 
# ------------------------------------------------------------
# LLM BULLET GENERATOR (unchanged)
# ------------------------------------------------------------
def llm_synthesize_slide(user_answers, global_prompt):
   qa_text = "\n".join(
       f"Q: {q}\nA: {a}"
       for q, a in user_answers.items()
       if a.strip()
   )
   prompt = f"""
You are a senior consultant creating a professional PowerPoint slide.
GLOBAL CONTEXT:
{global_prompt}
USER INPUT (rewrite professionally):
{qa_text}
TASK:
- derive a slide title
- derive 4–6 bullets
- rewrite clearly
- professional business tone
FORMAT:
Title: <title>
- bullet
- bullet
"""
   resp = text_client.chat.completions.create(
       model=get_env("CHAT_MODEL", required=True),
       messages=[{"role": "user", "content": prompt}],
       max_tokens=500,
       temperature=0.7,
   )
   raw = resp.choices[0].message.content.strip()
   lines = [x.strip() for x in raw.split("\n") if x.strip()]
   title = "Slide"
   bullets = []
   for ln in lines:
       if ln.lower().startswith("title"):
           title = ln.split(":", 1)[1].strip()
       elif ln.startswith("-"):
           bullets.append(ln[1:].strip())
   if not bullets:
       bullets = ["Content could not be generated"]
   return title, bullets
 
# ============================================================
# MAIN PPT GENERATOR
# ============================================================
def generate_presentation(payload):
   slides = payload.get("slides", [])
   answers_map = payload.get("answers_map", {})
   if not slides:
       raise ValueError("No slides provided")
   prs = Presentation()
   global_prompt = "professional business presentation"
 
   # ---------------------------------------------------
   # LOOP THROUGH ALL USER SELECTED SLIDES
   # ---------------------------------------------------
   for slide in slides:
    slide_idx = str(slide["slide_index"])
    slide_title = slide["slide_title"]
    user_answers = answers_map.get(slide_idx, {})

    # -----------------------------------------------------------
    # CASE 1 — PRESENTATION TITLE SLIDE (ONLY FIRST SLIDE)
    # -----------------------------------------------------------
    if "What should be the title of this presentation?" in user_answers:
        title_text = user_answers[
            "What should be the title of this presentation?"
        ].strip()

        subtitle = None
        for v in user_answers.values():
            if "202" in v:
                subtitle = v.strip()
                break

        add_title_slide(prs, title_text, subtitle)
        continue   # 🚨 VERY IMPORTANT

    # -----------------------------------------------------------
    # FROM HERE ON → ALL NON-TITLE SLIDES
    # -----------------------------------------------------------
    ppt_slide = prs.slides.add_slide(prs.slide_layouts[1])

    # -----------------------------------------------------------
    # CASE 2 — USER SKIPPED ANSWERS
    # -----------------------------------------------------------
    valid_answers_exist = any(v.strip() for v in user_answers.values())
    if not valid_answers_exist:
        ppt_slide.shapes.title.text = slide_title
        continue

    # -----------------------------------------------------------
    # CASE 3 — NORMAL CONTENT GENERATION
    # -----------------------------------------------------------
    try:
        llm_title, bullets = llm_synthesize_slide(
            user_answers,
            global_prompt
        )
    except Exception:
        logger.exception("LLM failed")
        bullets = ["Content could not be generated"]

    ppt_slide.shapes.title.text = slide_title
    body = ppt_slide.placeholders[1].text_frame
    body.clear()

    for b in bullets:
        para = body.add_paragraph()
        para.text = b
        para.level = 0
        para.font.size = Pt(18)
 
   # -----------------------------------------------------------
   # OPTIONAL ENDING SLIDE
   # -----------------------------------------------------------
   thanks = prs.slides.add_slide(prs.slide_layouts[1])
   thanks.shapes.title.text = "Thank You"
   #thanks.placeholders[1].text = "Questions?"
 
   # -----------------------------------------------------------
   # SAVE OUT FILE
   # -----------------------------------------------------------
   os.makedirs("generated", exist_ok=True)
   out_path = f"generated/ppt_{uuid.uuid4().hex[:6]}.pptx"
   prs.save(out_path)
   return out_path
