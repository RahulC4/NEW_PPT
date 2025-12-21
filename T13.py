<script>
const ul = document.getElementById("{slide_dom_id}_bullets");

ul.addEventListener("keydown", function (e) {
    const li = document.getSelection().anchorNode?.closest("li");
    if (!li) return;

    // ENTER → create new bullet
    if (e.key === "Enter") {
        e.preventDefault();

        const newLi = document.createElement("li");
        newLi.contentEditable = "true";
        newLi.innerText = "";

        li.after(newLi);

        const range = document.createRange();
        range.selectNodeContents(newLi);
        range.collapse(true);

        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    }

    // BACKSPACE on empty bullet → delete bullet
    if (e.key === "Backspace" && li.innerText.trim() === "") {
        e.preventDefault();

        const prev = li.previousElementSibling || li.nextElementSibling;
        li.remove();

        if (prev) {
            const range = document.createRange();
            range.selectNodeContents(prev);
            range.collapse(false);

            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        }
    }
});

// SAVE ON ANY CHANGE
document.addEventListener("input", () => {
    const title = document.getElementById("{slide_dom_id}_title").innerText;
    const bullets = [...ul.querySelectorAll("li")]
        .map(li => li.innerText)
        .filter(t => t.trim().length > 0);

    window.parent.postMessage({
        slideIndex: {i},
        title,
        bullets
    }, "*");
});
</script>
