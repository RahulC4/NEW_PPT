# ============================================================
# generate_ppt.py – Corporate path (QNA-DRIVEN)
# Title + Content strictly from Q&A
# Agenda logic untouched
# ============================================================

import os
import re
import uuid
import json
import tempfile
from typing import Dict, List, Any
from datetime import datetime

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from utils import get_env, logger, now_ts, ensure_dir, text_client
from azure_blob_utils import upload_ppt_to_blob, upload_json_to_blob

# --- optional Streamlit session fallback ---
try:
    import streamlit as st
    _SESSION = st.session_state
except Exception:
    _SESSION = {}

ensure_dir("generated")
CHAT_MODEL = get_env("CHAT_MODEL", required=True)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _from_session(key, default=None):
    try:
        return _SESSION.get(key, default)
    except Exception:
        return default


def _extract_answers_map(payload: Dict[str, Any]) -> Dict[str, Any]:
    return (
        payload.get("answers_by_slide")
        or _from_session("answers_by_slide")
        or {}
    )


def _answers_to_text(block: Dict[str, Any]) -> str:
    """
    Convert Q&A dict → clean text block
    Skips empty / 'not sure' answers
    """
    if not isinstance(block, dict):
        return ""

    lines = []
    for q, a in block.items():
        if not a:
            continue
        a = str(a).strip()
        if a.lower() in ("not sure", "na", "n/a"):
            continue
        lines.append(f"{q}: {a}")
    return "\n".join(lines)


def _is_title_slide(sel: Dict[str, Any]) -> bool:
    title = (sel.get("title") or "").lower()
    return "title" in title


# ------------------------------------------------------------
# LLM — QNA ONLY
# ------------------------------------------------------------
def _llm_generate_from_qna(qna_text: str, title_hint: str) -> Dict[str, Any]:
    """
    Generate bullets ONLY from Q&A
    """
    system_prompt = (
        "You are generating ONE presentation slide.\n"
        "STRICT RULES:\n"
        "- Use ONLY the provided Q&A content.\n"
        "- DO NOT invent or assume information.\n"
        "- Skip missing or unanswered points.\n"
        "- Create 3–6 concise bullets.\n\n"
        "FORMAT:\n"
        "Title: <short title>\n"
        "- Bullet\n"
        "- Bullet\n\n"
        f"Q&A Content:\n{qna_text}"
    )

    try:
        resp = text_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create the slide. Title hint: {title_hint}"},
            ],
            max_completion_tokens=700,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM failed, fallback used: {e}")
        return {
            "title": title_hint,
            "bullets": []
        }

    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    title = title_hint
    bullets = []

    for l in lines:
        if l.lower().startswith("title"):
            title = l.split(":", 1)[-1].strip()
        elif l.startswith("-"):
            bullets.append(l[1:].strip())

    return {
        "title": title_hint,
        "bullets": bullets
    }


# ------------------------------------------------------------
# PPT Builder
# ------------------------------------------------------------
def _build_ppt(slides: List[Dict[str, Any]]) -> str:
    prs = Presentation()

    for sp in slides:
        slide_type = sp.get("type")

        # ---- TITLE ----
        if slide_type == "title":
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            slide.shapes.title.text = sp["title"]
            continue

        # ---- AGENDA / CONTENT ----
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = sp["title"]

        tf = slide.shapes.placeholders[1].text_frame
        tf.clear()
        for b in sp.get("bullets", []):
            p = tf.add_paragraph()
            p.text = b
            p.font.size = Pt(20)
            p.level = 0

        # ---- THANK YOU ----
        if slide_type == "thankyou":
            slide.shapes.title.text = "Thank You"

    out = os.path.join(tempfile.gettempdir(), f"generated_{uuid.uuid4().hex[:8]}.pptx")
    prs.save(out)
    return out


# ------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------
def generate_presentation(payload: Dict[str, Any]) -> str:
    selected = (
        payload.get("selected_slide_structs")
        or _from_session("selected_slide_structs")
        or []
    )

    if not selected:
        raise ValueError("No slides selected")

    answers_map = _extract_answers_map(payload)
    slides_out = []

    # --------------------------------------------------------
    # 1️⃣ TITLE SLIDE (NO LLM)
    # --------------------------------------------------------
    for sel in selected:
        if _is_title_slide(sel):
            qna = answers_map.get(sel["slide_id"], {})
            title_text = next(iter(qna.values()), "Presentation")
            slides_out.append({
                "type": "title",
                "title": title_text.strip()
            })
            break

    # --------------------------------------------------------
    # 2️⃣ CONTENT SLIDES (QNA → LLM)
    # --------------------------------------------------------
    for sel in selected:
        if _is_title_slide(sel):
            continue

        slide_qna = answers_map.get(sel["slide_id"], {})
        qna_text = _answers_to_text(slide_qna)

        title_from_qna = next(iter(slide_qna.values()), sel.get("title"))

        slide_data = _llm_generate_from_qna(
            qna_text=qna_text,
            title_hint=title_from_qna
        )

        slides_out.append({
            "type": "content",
            "title": slide_data["title"],
            "bullets": slide_data["bullets"]
        })

    # --------------------------------------------------------
    # 3️⃣ THANK YOU
    # --------------------------------------------------------
    slides_out.append({
        "type": "thankyou",
        "title": "Thank You",
        "bullets": []
    })

    return _build_ppt(slides_out)
