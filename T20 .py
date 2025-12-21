st.markdown(
    """
    <script>
    window.getPreviewSlides = () => {
        const slides = [];
        document.querySelectorAll(".ppt-slide").forEach(slide => {
            const title = slide.querySelector(".ppt-title")?.innerText || "";
            const bullets = [...slide.querySelectorAll(".ppt-bullets li")]
                .map(li => li.innerText)
                .filter(t => t.trim().length > 0);

            slides.push({ title, bullets });
        });
        return slides;
    };
    </script>
    """,
    unsafe_allow_html=True
)




if st.button("🎯 Generate PPT"):
    # 🔥 pull latest edited content from DOM
    edited = st.components.v1.html(
        "<script>window.getPreviewSlides()</script>",
        height=0,
    )

    # fallback safety
    if edited:
        st.session_state["preview_slides"] = edited

    payload["preview_slides"] = st.session_state["preview_slides"]
    st.session_state["generation_payload"] = payload
    st.switch_page("pages/5_Generate_PPT.py")
