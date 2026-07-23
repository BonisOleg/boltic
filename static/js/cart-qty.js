(function () {
  "use strict";

  function parseIntSafe(value, fallback) {
    var n = parseInt(value, 10);
    return isNaN(n) ? fallback : n;
  }

  function clamp(value, min, max) {
    if (value < min) return min;
    if (max != null && value > max) return max;
    return value;
  }

  function snapToStep(value, min, step) {
    if (step < 1) step = 1;
    if (value < min) return min;
    var rem = (value - min) % step;
    if (rem === 0) return value;
    return value + (step - rem);
  }

  function syncButtons(form) {
    var input = form.querySelector("[data-qty-input]");
    if (!input) return;
    var min = parseIntSafe(input.getAttribute("min"), 1);
    var maxAttr = input.getAttribute("max");
    var max = maxAttr === null || maxAttr === "" ? null : parseIntSafe(maxAttr, null);
    var val = parseIntSafe(input.value, min);
    var minus = form.querySelector('[data-qty-delta^="-"]');
    var plus = form.querySelector('[data-qty-delta]:not([data-qty-delta^="-"])');
    if (minus) minus.disabled = val <= min;
    if (plus) plus.disabled = max != null && val >= max;
  }

  function applyValue(form, next, submitNow) {
    var input = form.querySelector("[data-qty-input]");
    if (!input) return;
    var min = parseIntSafe(input.getAttribute("min"), 1);
    var step = parseIntSafe(input.getAttribute("step"), min);
    var maxAttr = input.getAttribute("max");
    var max = maxAttr === null || maxAttr === "" ? null : parseIntSafe(maxAttr, null);
    var val = snapToStep(clamp(next, min, max), min, step);
    if (max != null && val > max) {
      val = Math.floor(max / step) * step;
      if (val < min) val = min;
    }
    input.value = String(val);
    syncButtons(form);
    if (submitNow) {
      if (typeof form.requestSubmit === "function") form.requestSubmit();
      else form.submit();
    }
  }

  function onDelta(form, delta) {
    var input = form.querySelector("[data-qty-input]");
    if (!input || form.dataset.submitting === "1") return;
    var min = parseIntSafe(input.getAttribute("min"), 1);
    var current = parseIntSafe(input.value, min);
    applyValue(form, current + delta, true);
  }

  function bindForm(form) {
    if (form.dataset.cartQtyBound === "1") return;
    form.dataset.cartQtyBound = "1";

    form.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-qty-delta]");
      if (!btn || !form.contains(btn) || btn.disabled) return;
      e.preventDefault();
      onDelta(form, parseIntSafe(btn.getAttribute("data-qty-delta"), 0));
    });

    var input = form.querySelector("[data-qty-input]");
    if (input) {
      input.addEventListener("change", function () {
        var min = parseIntSafe(input.getAttribute("min"), 1);
        applyValue(form, parseIntSafe(input.value, min), false);
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          var min = parseIntSafe(input.getAttribute("min"), 1);
          applyValue(form, parseIntSafe(input.value, min), true);
        }
      });
    }

    form.addEventListener("submit", function () {
      form.dataset.submitting = "1";
      var min = parseIntSafe(input && input.getAttribute("min"), 1);
      if (input) applyValue(form, parseIntSafe(input.value, min), false);
    });

    syncButtons(form);
  }

  function init() {
    var forms = document.querySelectorAll("form[data-cart-qty]");
    for (var i = 0; i < forms.length; i++) bindForm(forms[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
