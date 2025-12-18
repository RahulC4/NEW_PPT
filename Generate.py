
# ============================================================
# generate_ppt.py – Corporate path
# EXACTLY one output slide per user selection (no title/agenda/thank-you)
# Q&A-guided: paraphrase & enrich (never verbatim)
# Reads selection from payload OR st.session_state (fallback)
# Backward-compatible with legacy named-args calls
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

from utils import (
    get_env, logger, now_ts, ensure_dir, text_client  # Azure OpenAI chat client
)
from azure_blob_utils import upload_ppt_to_blob, upload_json_to_blob

# --- optional Streamlit session fallback ---
try:
    import streamlit as st  # only for session_state fallback
    _SESSION = st.session_state
except Exception:
    _SESSION = {}

ensure_dir("generated")
CHAT_MODEL = get_env("CHAT_MODEL", required=True)

# ---------- utils ----------
def _normalize_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, (tuple, set)):
        return list(x)
    if isinstance(x, dict):
        return [x]
    if isinstance(x, str):
        try:
            j = json.loads(x)
            return j if isinstance(j, list) else [j]
        except Exception:
            return [x]
    return []

def _from_session(key, default=None):
    try:
        return _SESSION.get(key, default)
    except Exception:
        return default

def _resolve_selection(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Robust resolver for selections:
      payload.selected_slide_structs
      payload.selected_slides + payload.slides_catalog/catalog/slides
      session_state.selected_slide_structs
      session_state.selected_slides + session_state.slides_catalog
      payload/SESSION slides[*].selected==True
      payload.selected_refs / payload.refs
      payload.selected_indices + catalog
      payload.selected_titles + catalog
      payload.selected (single)
      fallback: first num_slides from catalog
    """
    # ---- 1) payload: structs ----
    sstructs = payload.get("selected_slide_structs")
    if sstructs:
        return _normalize_list(sstructs)

    # ---- 2) payload: ids + catalog ----
    ids = _normalize_list(payload.get("selected_slides"))
    catalog = payload.get("slides_catalog") or payload.get("catalog") or payload.get("slides") or []
    catalog = _normalize_list(catalog)
    if ids and catalog:
        idset = set([i.get("slide_id", i) if isinstance(i, dict) else i for i in ids])
        return [s for s in catalog if s.get("slide_id") in idset]

    # ---- 3) session: structs ----
    sstructs = _from_session("selected_slide_structs")
    if sstructs:
        return _normalize_list(sstructs)

    # ---- 4) session: ids + catalog ----
    ids = _normalize_list(_from_session("selected_slides"))
    catalog = _normalize_list(_from_session("slides_catalog"))
    if ids and catalog:
        idset = set([i.get("slide_id", i) if isinstance(i, dict) else i for i in ids])
        return [s for s in catalog if s.get("slide_id") in idset]

    # ---- 5) slides[*].selected True ----
    if catalog:
        flagged = [s for s in catalog if s.get("selected") is True]
        if flagged:
            return flagged

    # ---- 6) other payload shapes ----
    idxs = _normalize_list(payload.get("selected_indices"))
    if idxs and catalog:
        try:
            idxs = [int(i) for i in idxs]
            return [s for i, s in enumerate(catalog) if i in idxs]
        except Exception:
            pass

    titles = _normalize_list(payload.get("selected_titles"))
    if titles and catalog:
        tset = set(titles)
        return [s for s in catalog if s.get("title") in tset]

    refs = payload.get("selected_refs") or payload.get("refs")
    if refs:
        return _normalize_list(refs)

    sel_one = payload.get("selected")
    if sel_one:
        return _normalize_list(sel_one)

    # ---- 7) fallback: first num_slides from catalog or session catalog ----
    num = int(payload.get("num_slides") or 0)
    if not catalog:
        catalog = _normalize_list(_from_session("slides_catalog"))
    if catalog and num > 0:
        logger.warning("Selection not found in payload; using first num_slides from catalog.")
        return catalog[:num]

    return []

def _extract_answers_map(payload: Dict[str, Any]) -> Dict[str, Any]:
    answers = (
        payload.get("answers_by_slide")
        or payload.get("answersBySlide")
        or payload.get("answers_per_slide")
        or payload.get("answersPerSlide")
        or _from_session("answers_by_slide")
        or {}
    )
    return answers if isinstance(answers, dict) else {}

def _extract_global_qna(payload: Dict[str, Any]) -> Dict[str, Any]:
    qna = (
        payload.get("qna_answers")
        or payload.get("answers")
        or payload.get("qna")
        or _from_session("qna_answers")
        or {}
    )
    return qna if isinstance(qna, dict) else {}

def _compose_guidance_text(sel: Dict[str, Any]) -> str:
    base = (sel.get("text") or sel.get("title") or "").strip()
    return base[:1200]

def _qna_to_block(qna: Dict[str, Any]) -> str:
    if isinstance(qna, dict):
        return "\n".join(f"{k}: {v}" for k, v in qna.items() if v)
    return str(qna or "")

def _answers_map_to_block(slide_id: str, answers_map: Dict[str, Any]) -> str:
    data = answers_map.get(slide_id)
    if isinstance(data, dict):
        return "\n".join(f"{k}: {v}" for k, v in data.items() if v)
    return str(data or "")

# ---------- LLM (one slide per selection) ----------
def _llm_enhance_single_slide(guidance_text: str, qna_block: str, per_slide_block: str, title_hint: str) -> Dict[str, Any]:
    sys_prompt = (
        "You are a senior presentation writer.\n"
        "Create ONE enhanced slide using the guidance below.\n"
        "- Use the reference and Q&A guidance only to form ideas; DO NOT copy sentences verbatim.\n"
        "- Produce a short title and 3–6 bullets (10–18 words, concrete, scannable).\n"
        "- Keep strictly to one slide.\n\n"
        "FORMAT:\n"
        "Slide 1: <Title>\n"
        "- Bullet\n"
        "- Bullet\n"
        "- Bullet\n\n"
        f"Reference (selected slide):\n{guidance_text}\n\n"
        f"Global Q&A (guidance only):\n{qna_block}\n\n"
        f"This slide's Q&A (guidance only):\n{per_slide_block}\n\n"
        "Never quote Q&A or reference sentences verbatim. Paraphrase and enrich.\n"
    )
    user_prompt = f"Create the enhanced slide now. Title hint: {title_hint or 'N/A'}"

    try:
        resp = text_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=900,
            temperature=0.9,
        )
        raw = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM failed → fallback used: {e}")
        return {
            "title": title_hint or "Enhanced Slide",
            "bullets": [
                "Objective summarized in practical terms.",
                "Rationale aligned to stakeholder priorities.",
                "Actionable next step informed by Q&A context.",
            ],
        }

    blocks = re.split(r"\n(?=Slide\s+1\s*:)", raw)
    lines = [l.strip() for l in blocks[0].split("\n") if l.strip()] if blocks else []
    if not lines:
        return {
            "title": title_hint or "Enhanced Slide",
            "bullets": [
                "Context synthesized and clarified.",
                "Solution approach summarized succinctly.",
                "Next step recommended.",
            ],
        }
    title = lines[0].split(":", 1)[-1].strip() or title_hint or "Enhanced Slide"
    bullets = [l[1:].strip() for l in lines[1:] if l.startswith("-")]
    if not bullets:
        bullets = [
            "Context synthesized and clarified.",
            "Solution approach summarized succinctly.",
            "Next step recommended.",
        ]
    return {"title": title, "bullets": bullets[:6]}

# ---------- Build exactly N slides (no title/agenda/thank-you) ----------
def _build_corporate_selected(slides: List[Dict[str, Any]]) -> str:
    prs = Presentation()
    for sp in slides:
        layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
        s = prs.slides.add_slide(layout)

        # Title styling (corporate)
        s.shapes.title.text = sp["title"]
        ttf = s.shapes.title.text_frame
        p = ttf.paragraphs[0]
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 102, 204)

        # Body bullets
        if len(s.placeholders) > 1:
            body = s.placeholders[1]
        else:
            body = s.shapes.add_textbox(Inches(1), Inches(2), prs.slide_width - Inches(2), Inches(4))
        tf = body.text_frame
        tf.clear()
        tf.word_wrap = True
        for b in sp.get("bullets", []):
            bp = tf.add_paragraph()
            bp.text = b
            bp.font.size = Pt(20)
            bp.level = 0

    out_path = os.path.join(tempfile.gettempdir(), f"generated_{uuid.uuid4().hex[:8]}.pptx")
    prs.save(out_path)
    return out_path

# ---------- PUBLIC API ----------
def generate_presentation(*args, **kwargs):
    """
    New payload mode: generate_presentation(payload_dict) -> str path
      - EXACTLY one output slide per selected reference (same order).
      - Q&A-guided (paraphrase; never verbatim).
      - Reads from payload OR st.session_state.
    Legacy named-args mode: returns (path, log).
    """
    # Payload mode
    if args and isinstance(args[0], dict):
        payload = args[0]
        selected = _resolve_selection(payload)
        if not selected:
            logger.error(
                "No selected slides found. Payload keys=%s | session keys=%s",
                list(payload.keys()), list(getattr(_SESSION, "keys", lambda: [])())
            )
            raise ValueError("No selected slides in payload or session_state.")

        answers_map = _extract_answers_map(payload)
        global_qna = _extract_global_qna(payload)
        qna_block = _qna_to_block(global_qna)

        enhanced = []
        for i, sel in enumerate(selected):
            guidance_text = _compose_guidance_text(sel)
            per_slide_block = _answers_map_to_block(sel.get("slide_id", ""), answers_map)
            title_hint = sel.get("title") or f"Selected Slide {i+1}"
            enhanced.append(_llm_enhance_single_slide(guidance_text, qna_block, per_slide_block, title_hint))

        out_path = _build_corporate_selected(enhanced[:len(selected)])
        return out_path  # string path

    # Legacy mode (named args)
    prompt = kwargs.get("prompt", "")
    requested_num_slides = int(kwargs.get("requested_num_slides") or 5)
    qna_answers = kwargs.get("qna_answers") or {}
    image_required = bool(kwargs.get("image_required", False))
    template_style = kwargs.get("template_style")

    global_qna = qna_answers
    qna_block = _qna_to_block(global_qna)
    selected = [{"title": prompt or "Slide", "text": prompt or ""} for _ in range(requested_num_slides)]

    enhanced = []
    for i, sel in enumerate(selected):
        enhanced.append(_llm_enhance_single_slide(_compose_guidance_text(sel), qna_block, "", sel.get("title") or f"Slide {i+1}"))

    out_path = _build_corporate_selected(enhanced[:requested_num_slides])

       # Legacy log + upload
    fname = f"generated_{uuid.uuid4().hex[:8]}.pptx"
    try:
        with open(out_path, "rb") as fh:
            upload_ppt_to_blob(fh.read(), fname)  # upload bytes
        upload_json_to_blob(json.dumps({
            "timestamp": now_ts(),
            "prompt": prompt,
            "slides_generated": requested_num_slides,
            "ppt_file": fname,
            "image_required": image_required,
            "template_style": template_style,
            "error": False,
        }, indent=2).encode("utf-8"), f"logs/{fname}.json")
    except Exception as e:
        logger.warning(f"Blob upload failed: {e}")

    return out_path, {
        "timestamp": now_ts(),
        "prompt": prompt,
        "slides_generated": requested_num_slides,
        "ppt_file": fname,
        "image_required": image_required,
        "template_style": template_style,
        "error": False,
    }
