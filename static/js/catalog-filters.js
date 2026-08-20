(function () {
  "use strict";

  var MQ = "(max-width: 899px)";
  var drawer = document.querySelector("[data-filter-drawer]");
  if (!drawer) return;

  var openBtn = document.querySelector("[data-filter-open]");
  var panel = drawer.querySelector("[data-filter-panel]");

  function isMobile() {
    return window.matchMedia(MQ).matches;
  }

  function setOpen(open) {
    if (!isMobile() && open) {
      open = false;
    }
    drawer.classList.toggle("is-open", open);
    document.body.classList.toggle("is-filter-drawer-open", open && isMobile());
    if (openBtn) {
      openBtn.setAttribute("aria-expanded", open ? "true" : "false");
    }
    if (panel) {
      panel.setAttribute("aria-hidden", open || !isMobile() ? "false" : "true");
    }
  }

  function close() {
    setOpen(false);
  }

  function open() {
    if (!isMobile()) return;
    setOpen(true);
  }

  if (openBtn) {
    openBtn.addEventListener("click", function () {
      if (drawer.classList.contains("is-open")) close();
      else open();
    });
  }

  drawer.querySelectorAll("[data-filter-close]").forEach(function (el) {
    el.addEventListener("click", close);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && drawer.classList.contains("is-open")) {
      close();
    }
  });

  window.matchMedia(MQ).addEventListener("change", function (ev) {
    if (!ev.matches) close();
  });

  /* Cold load: always closed on mobile */
  close();
})();
