(() => {
  const root = document.querySelector("[data-contact-branches]");
  if (!root) return;

  const list = root.querySelector("[data-branches-list]");
  const addBtn = root.querySelector("[data-branches-add]");
  const totalInput = root.querySelector('input[name="contact_branches-TOTAL_FORMS"]');
  if (!list || !addBtn || !totalInput) return;

  const PREFIX = "contact_branches";

  function reindex() {
    const rows = [...list.querySelectorAll("[data-branch-row]")];
    rows.forEach((row, index) => {
      row.querySelectorAll("input, textarea, select, label").forEach((el) => {
        ["name", "id", "for"].forEach((attr) => {
          const val = el.getAttribute(attr);
          if (!val) return;
          el.setAttribute(
            attr,
            val.replace(new RegExp(`${PREFIX}-\\d+-`), `${PREFIX}-${index}-`)
          );
        });
      });
      const sort = row.querySelector(`input[name$="-sort_order"]`);
      if (sort) sort.value = String(index);
    });
    totalInput.value = String(rows.length);
  }

  addBtn.addEventListener("click", () => {
    const index = Number(totalInput.value);
    const last = list.querySelector("[data-branch-row]:last-child");
    if (!last) return;
    const clone = last.cloneNode(true);
    clone.classList.remove("contact-branch-row--invalid");
    clone.querySelectorAll(".site-content-editor__errors").forEach((el) => el.remove());
    clone.querySelectorAll("input, textarea").forEach((el) => {
      if (el.type === "checkbox") {
        el.checked = el.name.endsWith("-is_active");
        return;
      }
      if (el.type === "hidden" && el.name && el.name.endsWith("-id")) {
        el.value = "";
        return;
      }
      if (el.type === "hidden" && el.name && el.name.endsWith("-DELETE")) {
        el.checked = false;
        el.value = "";
        return;
      }
      if (el.type !== "hidden" || (el.name && el.name.endsWith("-sort_order"))) {
        el.value = el.name && el.name.endsWith("-sort_order") ? String(index) : "";
      }
    });
    list.appendChild(clone);
    reindex();
    list.querySelectorAll("[data-branch-handle]").forEach((h) => {
      h.setAttribute("draggable", "true");
    });
  });

  let dragEl = null;
  list.querySelectorAll("[data-branch-handle]").forEach((h) => {
    h.setAttribute("draggable", "true");
  });
  list.addEventListener("dragstart", (e) => {
    const handle = e.target.closest("[data-branch-handle]");
    if (!handle) return;
    dragEl = handle.closest("[data-branch-row]");
    if (dragEl) dragEl.classList.add("is-dragging");
  });
  list.addEventListener("dragover", (e) => {
    e.preventDefault();
    const row = e.target.closest("[data-branch-row]");
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
