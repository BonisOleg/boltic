(function () {
  "use strict";

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function rawNum(raw) {
    var text = String(raw == null ? "" : raw).trim().replace(",", ".");
    if (!text) return "";
    var n = Number(text);
    if (!isFinite(n)) return text;
    return String(parseFloat(n.toFixed(4)));
  }

  function fmtNum(raw) {
    var key = rawNum(raw);
    if (!key) return "";
    var n = Number(key);
    if (!isFinite(n)) return key;
    return String(parseFloat(n.toFixed(2)));
  }

  function normalize(text) {
    return String(text || "")
      .toLowerCase()
      .replace(/×/g, "x")
      .replace(/\s+/g, "")
      .replace(/,/g, ".");
  }

  function uniqueSorted(values) {
    var map = {};
    values.forEach(function (v) {
      var key = rawNum(v);
      if (!key) return;
      map[key] = true;
    });
    return Object.keys(map).sort(function (a, b) {
      return Number(a) - Number(b);
    });
  }

  function initSkuFilter(root) {
    var table = qs("[data-sku-table]", root) || qs(".data-table--sku", root.parentElement);
    if (!table) return;

    var tbody = qs("tbody", table);
    var rows = qsa("tr[data-sku-row]", tbody);
    if (rows.length < 2) {
      root.hidden = true;
      return;
    }

    var qInput = qs("[data-sku-q]", root);
    var clearQ = qs("[data-sku-clear-q]", root);
    var diaWrap = qs("[data-sku-diameters]", root);
    var lenWrap = qs("[data-sku-lengths]", root);
    var diaRow = qs("[data-sku-diameter-row]", root);
    var lenRow = qs("[data-sku-length-row]", root);
    var stockInput = qs("[data-sku-stock]", root);
    var countEl = qs("[data-sku-count]", root);
    var resetBtn = qs("[data-sku-reset]", root);
    var emptyEl = qs("[data-sku-empty]", root.parentElement) || qs("[data-sku-empty]");

    var state = {
      q: "",
      diameter: "",
      length: "",
      inStockOnly: false,
    };

    var useMetricM = root.getAttribute("data-metric-m") === "1";

    var diameters = uniqueSorted(
      rows.map(function (r) {
        return r.getAttribute("data-diameter");
      })
    );
    var allLengths = uniqueSorted(
      rows.map(function (r) {
        return r.getAttribute("data-length");
      })
    );

    function lengthsForDiameter(diameter) {
      if (!diameter) return allLengths;
      return uniqueSorted(
        rows
          .filter(function (r) {
            return rawNum(r.getAttribute("data-diameter")) === diameter;
          })
          .map(function (r) {
            return r.getAttribute("data-length");
          })
      );
    }

    function makeChip(value, label, kind) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sku-filter__chip";
      btn.setAttribute("data-sku-chip", kind);
      btn.setAttribute("data-value", value);
      btn.setAttribute("aria-pressed", "false");
      btn.textContent = label;
      return btn;
    }

    function renderDiameterChips() {
      if (!diaWrap) return;
      diaWrap.innerHTML = "";
      if (diameters.length < 2) {
        if (diaRow) diaRow.hidden = true;
        return;
      }
      if (diaRow) diaRow.hidden = false;
      diameters.forEach(function (d) {
        var label = useMetricM ? "M" + fmtNum(d) : fmtNum(d);
        diaWrap.appendChild(makeChip(d, label, "diameter"));
      });
    }

    function renderLengthChips() {
      if (!lenWrap) return;
      var lengths = lengthsForDiameter(state.diameter);
      lenWrap.innerHTML = "";
      if (lengths.length < 2 && !state.diameter) {
        if (lenRow) lenRow.hidden = true;
        return;
      }
      if (lengths.length === 0) {
        if (lenRow) lenRow.hidden = true;
        return;
      }
      if (lenRow) lenRow.hidden = false;
      lengths.forEach(function (l) {
        lenWrap.appendChild(makeChip(l, fmtNum(l) + " мм", "length"));
      });
      if (state.length && lengths.indexOf(state.length) === -1) {
        state.length = "";
      }
      syncChipActive();
    }

    function syncChipActive() {
      qsa("[data-sku-chip]", root).forEach(function (btn) {
        var kind = btn.getAttribute("data-sku-chip");
        var value = btn.getAttribute("data-value");
        var active =
          (kind === "diameter" && value === state.diameter) ||
          (kind === "length" && value === state.length);
        btn.classList.toggle("is-active", active);
        btn.setAttribute("aria-pressed", active ? "true" : "false");
      });
    }

    function isActive() {
      return Boolean(
        state.q || state.diameter || state.length || state.inStockOnly
      );
    }

    function apply() {
      var q = normalize(state.q);
      var visible = 0;

      rows.forEach(function (row) {
        var hay = normalize(
          [
            row.getAttribute("data-size") || "",
            row.getAttribute("data-article") || "",
            row.getAttribute("data-name") || "",
          ].join(" ")
        );
        var ok = true;
        if (q && hay.indexOf(q) === -1) ok = false;
        if (ok && state.diameter && rawNum(row.getAttribute("data-diameter")) !== state.diameter) {
          ok = false;
        }
        if (ok && state.length && rawNum(row.getAttribute("data-length")) !== state.length) {
          ok = false;
        }
        if (ok && state.inStockOnly && row.getAttribute("data-stock") !== "in_stock") {
          ok = false;
        }
        row.classList.toggle("is-filtered-out", !ok);
        if (ok) visible += 1;
      });

      if (countEl) {
        countEl.textContent =
          visible === rows.length
            ? rows.length + " позицій"
            : "Знайдено " + visible + " з " + rows.length;
      }
      if (resetBtn) resetBtn.hidden = !isActive();
      if (clearQ) clearQ.hidden = !state.q;
      if (emptyEl) emptyEl.hidden = visible !== 0;
      syncChipActive();
    }

    function reset() {
      state.q = "";
      state.diameter = "";
      state.length = "";
      state.inStockOnly = false;
      if (qInput) qInput.value = "";
      if (stockInput) stockInput.checked = false;
      renderLengthChips();
      apply();
      if (qInput) qInput.focus();
    }

    root.addEventListener("click", function (e) {
      var chip = e.target.closest("[data-sku-chip]");
      if (chip && root.contains(chip)) {
        var kind = chip.getAttribute("data-sku-chip");
        var value = chip.getAttribute("data-value") || "";
        if (kind === "diameter") {
          state.diameter = state.diameter === value ? "" : value;
          state.length = "";
          renderLengthChips();
        } else if (kind === "length") {
          state.length = state.length === value ? "" : value;
        }
        apply();
        return;
      }
      if (e.target.closest("[data-sku-reset]")) {
        reset();
      }
      if (e.target.closest("[data-sku-clear-q]")) {
        state.q = "";
        if (qInput) qInput.value = "";
        apply();
        if (qInput) qInput.focus();
      }
    });

    if (qInput) {
      qInput.addEventListener("input", function () {
        state.q = qInput.value.trim();
        apply();
      });
      qInput.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          if (state.q) {
            state.q = "";
            qInput.value = "";
            apply();
          }
        }
      });
    }

    if (stockInput) {
      stockInput.addEventListener("change", function () {
        state.inStockOnly = stockInput.checked;
        apply();
      });
    }

    renderDiameterChips();
    renderLengthChips();
    apply();
  }

  function boot() {
    qsa("[data-sku-filter]").forEach(initSkuFilter);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
