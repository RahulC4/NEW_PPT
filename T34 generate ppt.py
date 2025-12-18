# ============================================================
# generate_ppt.py – FINAL CORPORATE FLOW (Q&A DRIVEN)
# ============================================================

import os
import uuid
import tempfile
import json
import re
from typing import Dict, List, Any

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from utils import get_env, logger, text_client

# Optional Streamlit fallback
try:
    import streamlit as st
    SESSION = st.session_state
except Exception:
    SESSION = {}

CHAT_MODEL = get_env("CHAT_MODEL", required=True)


# ============================================================
# ----------- PAYLOAD HELPERS
# ============================================================

def _safe_dict(x):
    return x if isinstance(x, dict) else {}

def _safe_list(x):
    return x if isinstance(x, list) else []

def _get_answers_map(payload):
    return (
        payload.get("answers_by_slide")
        or payload.get("answersPerSlide")
        or SESSION.get("answers_by_slide")
        or {}
    )

def _get_global_qna(payload):
    return (
        payload.get("qna_answers")
        or payload.get("answers")
        or SESSION.get("qna_answers")
        or {}
    )

def _resolve_selected_slide_structs(payload):
    """
    MUST return full slide structs from slides_catalog
    """
    # 1️⃣ Explicit payload
    if payload.get("selected_slide_structs"):
        return payload["selected_slide_structs"]

    # 2️⃣ Rebuild from catalog + selected IDs
    selected_ids = (
        payload.get("selected_slides")
        or SESSION.get("selected_slides")
        or []
    )

    catalog = (
        payload.get("slides_catalog")
        or SESSION.get("slides_catalog")
        or []
    )

    selected = [s for s in catalog if s.get("slide_id") in selected_ids]

    if not selected:
        raise ValueError("No selected slide structs found")

    return selected


# ============================================================
# ----------- LLM CONTENT GENERATION
# ============================================================

def _llm_generate_bullets(slide_title, qna_block, slide_qna_block):
    system_prompt = f"""
You are a senior presentation writer.

GOAL:
Create bullet points for ONE slide.

RULES:
- Title is FIXED and MUST NOT be changed
- Use Q&A context to infer intent
- Do NOT copy Q&A verbatim
- Skip unanswered questions
- Generate 3–6 concise bullets
- Professional corporate tone

Slide title:
{slide_title}

Global Q&A:
{qna_block}

Slide-specific Q&A:
{slide_qna_block}
"""

    resp = text_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate bullet points only."},
        ],
        temperature=0.7,
        max_completion_tokens=500,
    )

    text = resp.choices[0].message.content.strip()
    bullets = [l.strip("- ").strip() for l in text.split("\n") if l.strip()]
    return bullets[:6]


# ============================================================
# ----------- PPT BUILDERS
# ============================================================

def _add_title_slide(prs, title_text):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    box = slide.shapes.add_textbox(
        Inches(2), Inches(3), prs.slide_width - Inches(4), Inches(2)
    )
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 102, 204)
    p.alignment = 1  # CENTER


def _add_agenda_slide(prs, titles):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Agenda"
    tf = slide.placeholders[1].text_frame
    tf.clear()

    for t in titles:
        p = tf.add_paragraph()
        p.text = t
        p.font.size = Pt(20)
        p.level = 0


def _add_content_slide(prs, title, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title
    tf = slide.placeholders[1].text_frame
    tf.clear()

    for b in bullets:
        p = tf.add_paragraph()
        p.text = b
        p.font.size = Pt(18)
        p.level = 0


def _add_thank_you_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.add_textbox(
        Inches(3), Inches(3),
        prs.slide_width - Inches(6), Inches(2)
    ).text_frame.text = "Thank You"


# ============================================================
# ----------- MAIN ENTRY
# ============================================================

def generate_presentation(payload: Dict[str, Any]) -> str:
    """
    FINAL FLOW:
    1. Title slide → from TITLE Q&A answer ONLY
    2. Agenda slide → titles from reference slides
    3. Content slides → title from reference, bullets from Q&A
    4. Thank You slide
    """

    prs = Presentation()

    # ---------- Extract data ----------
    answers_map = _get_answers_map(payload)
    global_qna = _get_global_qna(payload)
    selected_slides = _resolve_selected_slide_structs(payload)

    # ---------- TITLE SLIDE ----------
    title_answer = ""
    for v in global_qna.values():
        if isinstance(v, str) and v.strip():
            title_answer = v.strip()
            break

    if not title_answer:
        title_answer = "Presentation"

    _add_title_slide(prs, title_answer)

    # ---------- AGENDA ----------
    agenda_titles = [s.get("title", "Slide") for s in selected_slides]
    _add_agenda_slide(prs, agenda_titles)

    # ---------- CONTENT SLIDES ----------
    global_qna_block = "\n".join(
        f"{k}: {v}" for k, v in global_qna.items() if v
    )

    for s in selected_slides:
        slide_id = s.get("slide_id")
        slide_title = s.get("title", "Slide")

        slide_qna = answers_map.get(slide_id, {})
        slide_qna_block = "\n".join(
            f"{k}: {v}" for k, v in slide_qna.items() if v
        )

        bullets = _llm_generate_bullets(
            slide_title,
            global_qna_block,
            slide_qna_block
        )

        _add_content_slide(prs, slide_title, bullets)

    # ---------- THANK YOU ----------
    _add_thank_you_slide(prs)

    # ---------- SAVE ----------
    out_path = os.path.join(
        tempfile.gettempdir(),
        f"generated_{uuid.uuid4().hex[:8]}.pptx"
    )
    prs.save(out_path)
    return out_path
