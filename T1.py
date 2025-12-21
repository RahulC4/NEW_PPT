st.markdown(
    """
    <script>
    window.collectPreviewSlides = () => {
        const slides = [];
        document.querySelectorAll("[id$='_bullets']").forEach((ul, idx) => {
            const title = document.getElementById(`slide_${idx}_title`)?.innerText || "";
            const bullets = [...ul.querySelectorAll("li")]
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



with col2:
    if st.button("🎯 Generate PPT"):
        # 🔥 FORCE final DOM → Python sync
        edited = st.components.v1.html(
            "<script>window.collectPreviewSlides()</script>",
            height=0,
        )

        if edited:
            st.session_state["preview_slides"] = edited

        payload["slides"] = st.session_state["preview_slides"]
        st.session_state["generation_payload"] = payload
        st.switch_page("pages/5_Generate_PPT.py")
