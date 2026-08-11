(() => {
  const root = document.querySelector("[data-hero-slides]");
  if (!root) return;

  const list = root.querySelector("[data-hero-list]");
  const addBtn = root.querySelector("[data-hero-add]");
  const totalInput = root.querySelector('input[name="hero_slides-TOTAL_FORMS"]');
  if (!list || !addBtn || !totalInput) return;

  function reindex() {
    const rows = [...list.querySelectorAll("[data-hero-row]")];
    rows.forEach((row, index) => {
      row.querySelectorAll("input, textarea, select, label").forEach((el) => {
        ["name", "id", "for"].forEach((attr) => {
          const val = el.getAttribute(attr);
          if (!val) return;
          el.setAttribute(
            attr,
            val.replace(/hero_slides-\d+-/, `hero_slides-${index}-`)
          );
        });
      });
      const sort = row.querySelector('input[name$="-sort_order"]');
      if (sort) sort.value = String(index);
    });
    totalInput.value = String(rows.length);
  }

  addBtn.addEventListener("click", () => {
    const index = Number(totalInput.value);
    const empty = root.querySelector(".empty-form") || null;
    // Build from last row clone (extra form already in DOM as last)
    const last = list.querySelector("[data-hero-row]:last-child");
    if (!last) return;
    const clone = last.cloneNode(true);
    clone.querySelectorAll("input, textarea").forEach((el) => {
      if (el.type === "checkbox") {
        el.checked = el.name.endsWith("-is_active");
        return;
      }
      if (el.type === "hidden" && el.name && el.name.endsWith("-id")) {
        el.value = "";
        return;
      }
      if (el.type !== "hidden" || (el.name && el.name.endsWith("-sort_order"))) {
        el.value = el.name && el.name.endsWith("-sort_order") ? String(index) : "";
      }
    });
    clone.querySelectorAll("img.hero-slide-row__preview").forEach((img) => img.remove());
    list.appendChild(clone);
    reindex();
  });

  let dragEl = null;
  list.addEventListener("dragstart", (e) => {
    const handle = e.target.closest("[data-hero-handle]");
    if (!handle) return;
    dragEl = handle.closest("[data-hero-row]");
    if (dragEl) dragEl.classList.add("is-dragging");
  });
  list.querySelectorAll("[data-hero-handle]").forEach((h) => {
    h.setAttribute("draggable", "true");
  });
  list.addEventListener("dragover", (e) => {
    e.preventDefault();
    const row = e.target.closest("[data-hero-row]");
    if (!row || !dragEl || row === dragEl) return;
    const rect = row.getBoundingClientRect();
    const before = e.clientY < rect.top + rect.height / 2;
    list.insertBefore(dragEl, before ? row : row.nextSibling);
  });
  list.addEventListener("dragend", () => {
    if (dragEl) dragEl.classList.remove("is-dragging");
    dragEl = null;
    reindex();
  });
})();
