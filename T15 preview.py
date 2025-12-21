import streamlit as st
import uuid

st.set_page_config(page_title="4 - Preview Slides", layout="wide")
st.title("4 — Preview & Edit Slides")

# ---------------------------------------------------
# LOAD PAYLOAD (UNCHANGED)
# ---------------------------------------------------
payload = st.session_state.get("generation_payload")
if not payload:
    st.error("No generation payload found.")
    st.stop()

slides = payload.get("slides", [])
answers_map = payload.get("answers_map", {})

# ---------------------------------------------------
# RESET PREVIEW WHEN PAYLOAD CHANGES
# ---------------------------------------------------
payload_signature = tuple(
    (s["slide_index"], s["slide_title"])
    for s in slides
)

if st.session_state.get("_preview_signature") != payload_signature:
    st.session_state["preview_slides"] = []
    st.session_state["_preview_signature"] = payload_signature

# ---------------------------------------------------
# INIT PREVIEW STATE (LLM CONTENT ONLY – ONCE PER PAYLOAD)
# ---------------------------------------------------
if not st.session_state["preview_slides"]:
    preview = []
    for s in slides:
        slide_idx = str(s["slide_index"])
        user_answers = answers_map.get(slide_idx, {})

        bullets = [
            a.strip()
            for a in user_answers.values()
            if a and a.strip()
        ]

        preview.append({
            "slide_index": s["slide_index"],
            "title": s["slide_title"],
            "bullets": bullets[:6] or ["Click to edit bullet"]
        })

    st.session_state["preview_slides"] = preview

# ---------------------------------------------------
# RENDER SLIDES (HTML CANVAS – PPT STYLE)
# ---------------------------------------------------
for i, slide in enumerate(st.session_state["preview_slides"]):
    slide_dom_id = f"slide_{i}_{uuid.uuid4().hex[:6]}"

    bullets_html = "".join(
        f'<li contenteditable="true">{b}</li>'
        for b in slide["bullets"]
    )

    st.components.v1.html(
        f"""
        <div style="
            width:1280px;
            height:720px;
            border:1px solid #d0d0d0;
            padding:60px;
            margin:40px auto;
            font-family:Segoe UI, Arial;
            background:white;
            box-shadow:0 4px 12px rgba(0,0,0,0.08);
        ">

            <!-- TITLE -->
            <div contenteditable="true"
                 id="{slide_dom_id}_title"
                 style="
                    font-size:40px;
                    font-weight:600;
                    margin-bottom:30px;
                    outline:none;
                 ">
                {slide["title"]}
            </div>

            <!-- BULLETS -->
            <ul id="{slide_dom_id}_bullets"
                style="
                    font-size:22px;
                    line-height:1.6;
                    padding-left:30px;
                ">
                {bullets_html}
            </ul>
        </div>

        <script>
        const bulletsEl = document.getElementById("{slide_dom_id}_bullets");

        // ENTER = new bullet, BACKSPACE on empty = delete bullet
        bulletsEl.addEventListener("keydown", (e) => {{
            const li = document.getSelection()?.anchorNode?.closest("li");
            if (!li) return;

            // ENTER → create new bullet
            if (e.key === "Enter") {{
                e.preventDefault();
                const newLi = document.createElement("li");
                newLi.contentEditable = "true";
                newLi.innerText = "";
                li.after(newLi);

                const range = document.createRange();
                range.setStart(newLi, 0);
                range.collapse(true);
                const sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            }}

            // BACKSPACE on empty → delete bullet
            if (e.key === "Backspace" && li.innerText.trim() === "") {{
                e.preventDefault();
                const prev = li.previousElementSibling;
                li.remove();
                if (prev) {{
                    const range = document.createRange();
                    range.selectNodeContents(prev);
                    range.collapse(false);
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                }}
            }}
        }});

        const save = () => {{
            const title = document.getElementById("{slide_dom_id}_title").innerText;
            const bullets = [...document.querySelectorAll("#{slide_dom_id}_bullets li")]
                .map(li => li.innerText)
                .filter(t => t.trim().length > 0);

            window.parent.postMessage({{
                slideIndex: {i},
                title,
                bullets
            }}, "*");
        }};

        document.addEventListener("input", save);
        </script>
        """,
        height=800,
    )

# ---------------------------------------------------
# RECEIVE EDITS FROM JS (NO LOGIC CHANGE)
# ---------------------------------------------------
st.session_state.setdefault("preview_updates", {})

st.markdown(
    """
    <script>
    window.addEventListener("message", (event) => {{
        const data = event.data;
        if (data && data.slideIndex !== undefined) {{
            window.parent.streamlitSendMessage({{
                type: "preview_update",
                data: data
            }});
        }}
    }});
    </script>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# APPLY EDITS TO SESSION STATE
# ---------------------------------------------------
for msg in st.session_state.get("_streamlit_messages", []):
    if msg.get("type") == "preview_update":
        data = msg.get("data", {})
        idx = data.get("slideIndex")
        if idx is not None and idx < len(st.session_state["preview_slides"]):
            st.session_state["preview_slides"][idx]["title"] = data.get("title", "")
            st.session_state["preview_slides"][idx]["bullets"] = data.get("bullets", [])

# ---------------------------------------------------
# GENERATE BUTTON (UNCHANGED FLOW)
# ---------------------------------------------------
st.markdown("---")

if st.button("🎯 Generate PPT"):
    payload["preview_slides"] = st.session_state["preview_slides"]
    st.session_state["generation_payload"] = payload
    st.switch_page("pages/5_Generate_PPT.py")
