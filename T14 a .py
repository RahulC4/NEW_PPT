bulletsEl.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== "Backspace") return;

    const sel = window.getSelection();
    if (!sel || !sel.anchorNode) return;

    const li = sel.anchorNode.closest("li");
    if (!li) return;

    // ---------------------------
    // ENTER → create new bullet
    // ---------------------------
    if (e.key === "Enter") {
        e.preventDefault(); // 🚨 stops newline creation

        const newLi = document.createElement("li");
        newLi.contentEditable = "true";
        newLi.innerHTML = "";

        li.after(newLi);

        const range = document.createRange();
        range.setStart(newLi, 0);
        range.collapse(true);

        sel.removeAllRanges();
        sel.addRange(range);
        return;
    }

    // ---------------------------
    // BACKSPACE on empty → delete
    // ---------------------------
    if (e.key === "Backspace" && li.innerText.trim() === "") {
        e.preventDefault();

        const prev = li.previousElementSibling;
        li.remove();

        if (prev) {
            const range = document.createRange();
            range.selectNodeContents(prev);
            range.collapse(false);
            sel.removeAllRanges();
            sel.addRange(range);
        }
    }
});
