(function () {
  "use strict";

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /* Mega menu */
  var catalogBtn = qs("[data-catalog-toggle]");
  var mega = qs("[data-mega-menu]");
  var overlay = qs("[data-mega-overlay]");

  function setMegaMore(expanded) {
    if (!mega) return;
    var moreBtn = qs("[data-mega-more]", mega);
    var label = moreBtn ? qs("[data-mega-more-label]", moreBtn) : null;
    var list = qs("[data-mega-l1-list]", mega);
    mega.classList.toggle("is-expanded", expanded);
    if (moreBtn) {
      moreBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
    }
    if (label) {
      label.textContent = expanded ? "Згорнути" : "Більше категорій";
    }
    if (list) {
      if (expanded) {
        var firstExtra = qs(".mega-l1__item--extra", list);
        if (firstExtra) {
          firstExtra.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
      } else {
        list.scrollTop = 0;
      }
    }
  }

  function closeMega() {
    if (!mega) return;
    mega.classList.remove("is-open");
    setMegaMore(false);
    if (overlay) overlay.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  function openMega() {
    if (!mega) return;
    mega.classList.add("is-open");
    if (overlay) overlay.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }

  if (catalogBtn && mega) {
    catalogBtn.addEventListener("click", function (e) {
      e.preventDefault();
      if (mega.classList.contains("is-open")) closeMega();
      else openMega();
    });
  }
  if (overlay) overlay.addEventListener("click", closeMega);

  if (mega) {
    var moreToggle = qs("[data-mega-more]", mega);
    if (moreToggle) {
      moreToggle.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        setMegaMore(!mega.classList.contains("is-expanded"));
      });
    }
  }

  qsa("[data-mega-l1]").forEach(function (btn) {
    btn.addEventListener("mouseenter", function () {
      if (window.matchMedia("(max-width: 991px)").matches) return;
      var id = btn.getAttribute("data-mega-l1");
      qsa("[data-mega-l1]").forEach(function (b) {
        b.parentElement.classList.toggle("is-active", b === btn);
      });
      qsa("[data-mega-panel]").forEach(function (p) {
        p.classList.toggle("is-active", p.getAttribute("data-mega-panel") === id);
      });
    });
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-mega-l1");
      qsa("[data-mega-l1]").forEach(function (b) {
        b.parentElement.classList.toggle("is-active", b === btn);
      });
      qsa("[data-mega-panel]").forEach(function (p) {
        p.classList.toggle("is-active", p.getAttribute("data-mega-panel") === id);
      });
    });
  });

  /* Mobile drawer */
  var drawer = qs("[data-mobile-drawer]");
  var drawerToggle = qs("[data-mobile-toggle]");
  var drawerClose = qs("[data-mobile-close]");

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("is-open");
    if (overlay) overlay.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  if (drawerToggle && drawer) {
    drawerToggle.addEventListener("click", function () {
      drawer.classList.add("is-open");
      if (overlay) overlay.classList.add("is-open");
      document.body.style.overflow = "hidden";
    });
  }
  if (drawerClose) drawerClose.addEventListener("click", closeDrawer);
  if (overlay) {
    overlay.addEventListener("click", function () {
      closeDrawer();
      closeMega();
    });
  }

  /* Hero slider */
  var track = qs("[data-hero-track]");
  if (track) {
    var slides = qsa(".hero-slide", track);
    var idx = 0;
    function go(n) {
      if (!slides.length) return;
      idx = (n + slides.length) % slides.length;
      track.style.transform = "translateX(" + -idx * 100 + "%)";
    }
    var prev = qs("[data-hero-prev]");
    var next = qs("[data-hero-next]");
    if (prev) prev.addEventListener("click", function () { go(idx - 1); });
    if (next) next.addEventListener("click", function () { go(idx + 1); });
    if (slides.length > 1) {
      setInterval(function () { go(idx + 1); }, 6000);
    }
  }

  /* PDP tabs */
  qsa("[data-tab]").forEach(function (tab) {
    tab.addEventListener("click", function () {
      var name = tab.getAttribute("data-tab");
      qsa("[data-tab]").forEach(function (t) {
        t.classList.toggle("is-active", t === tab);
      });
      qsa("[data-panel]").forEach(function (p) {
        p.classList.toggle("is-active", p.getAttribute("data-panel") === name);
      });
    });
  });

  /* Scroll top — rAF throttle */
  var scrollTop = qs("[data-scroll-top]");
  if (scrollTop) {
    var scrollQueued = false;
    var scrollVisible = false;
    window.addEventListener(
      "scroll",
      function () {
        if (scrollQueued) return;
        scrollQueued = true;
        requestAnimationFrame(function () {
          scrollQueued = false;
          var show = window.scrollY > 400;
          if (show === scrollVisible) return;
          scrollVisible = show;
          scrollTop.classList.toggle("is-visible", show);
        });
      },
      { passive: true }
    );
    scrollTop.addEventListener("click", function () {
      window.scrollTo(0, 0);
    });
  }

  /* Escape closes overlays */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeMega();
      closeDrawer();
    }
  });

  /* Facet groups: collapse after 5 checkboxes */
  var FACET_VISIBLE = 5;

  function initFacetMore() {
    qsa("[data-facet-group]").forEach(function (group) {
      if (group.getAttribute("data-facet-ready")) return;
      var labels = qsa(".facet-group__list > label", group);
      if (labels.length <= FACET_VISIBLE) return;

      group.setAttribute("data-facet-ready", "1");

      var hasHiddenChecked = labels.some(function (label, i) {
        if (i < FACET_VISIBLE) return false;
        var input = qs('input[type="checkbox"]', label);
        return input && input.checked;
      });
      if (hasHiddenChecked) group.classList.add("is-expanded");

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "facet-group__more";
      btn.setAttribute("data-facet-more", "");

      function syncMoreBtn() {
        var expanded = group.classList.contains("is-expanded");
        var hiddenCount = labels.length - FACET_VISIBLE;
        btn.textContent = expanded
          ? "Показати менше"
          : "Показати більше (" + hiddenCount + ")";
        btn.setAttribute("aria-expanded", expanded ? "true" : "false");
      }

      syncMoreBtn();
      btn.addEventListener("click", function () {
        group.classList.toggle("is-expanded");
        syncMoreBtn();
      });
      group.appendChild(btn);
    });
  }

  /* Scroll reveal — sections only, no product grids */
  function initReveal() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) return;

    var nodes = qsa(
      ".page-main > .seo-block, .home-rail > .section-card, .home-rail > .seo-block, .services-row > .service-card, .advantages .advantage-item, .pdp-hero, .facets"
    );
    if (!nodes.length) return;

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          el.classList.add("is-visible");
          io.unobserve(el);
          function cleanup(e) {
            if (e && e.propertyName && e.propertyName !== "opacity") return;
            el.classList.remove("reveal");
            el.classList.remove("is-visible");
            el.removeEventListener("transitionend", cleanup);
          }
          el.addEventListener("transitionend", cleanup);
          window.setTimeout(cleanup, 450);
        });
      },
      { root: null, rootMargin: "0px 0px -6% 0px", threshold: 0.08 }
    );

    nodes.forEach(function (el) {
      el.classList.add("reveal");
      io.observe(el);
    });
  }

  function bootUi() {
    initFacetMore();
    initReveal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootUi);
  } else {
    bootUi();
  }
})();
