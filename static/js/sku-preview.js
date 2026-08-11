(function () {
  "use strict";

  var canHover =
    window.matchMedia &&
    window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  if (!canHover) return;

  var table = document.querySelector("[data-sku-table]");
  if (!table) return;

  var tip = document.createElement("div");
  tip.className = "sku-preview";
  tip.setAttribute("aria-hidden", "true");
  tip.innerHTML = '<img alt="" width="150" height="150" decoding="async">';
  document.body.appendChild(tip);

  var img = tip.querySelector("img");
  var activeLink = null;
  var hideTimer = null;

  function place(clientX, clientY) {
    var pad = 14;
    var w = tip.offsetWidth || 150;
    var h = tip.offsetHeight || 150;
    var x = clientX + pad;
    var y = clientY + pad;
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    if (x + w > vw - 8) x = clientX - w - pad;
    if (y + h > vh - 8) y = clientY - h - pad;
    if (x < 8) x = 8;
    if (y < 8) y = 8;
    tip.style.left = Math.round(x) + "px";
    tip.style.top = Math.round(y) + "px";
  }

  function show(link, clientX, clientY) {
    var src = link.getAttribute("data-sku-preview");
    if (!src) return;
    if (hideTimer) {
      clearTimeout(hideTimer);
      hideTimer = null;
    }
    if (img.getAttribute("src") !== src) {
      img.setAttribute("src", src);
    }
    activeLink = link;
    tip.classList.add("is-visible");
    place(clientX, clientY);
  }

  function hide() {
    activeLink = null;
    tip.classList.remove("is-visible");
  }

  function scheduleHide() {
    if (hideTimer) clearTimeout(hideTimer);
    hideTimer = setTimeout(hide, 40);
  }

  function previewLinkFrom(target) {
    if (!target || !target.closest) return null;
    var link = target.closest(".sku-name-link[data-sku-preview]");
    if (!link || !table.contains(link)) return null;
    return link;
  }

  table.addEventListener("mouseover", function (e) {
    var link = previewLinkFrom(e.target);
    if (!link) return;
    show(link, e.clientX, e.clientY);
  });

  table.addEventListener("mousemove", function (e) {
    if (!activeLink) return;
    var link = previewLinkFrom(e.target);
    if (link !== activeLink) return;
    place(e.clientX, e.clientY);
  });

  table.addEventListener("mouseout", function (e) {
    if (!activeLink) return;
    var to = e.relatedTarget;
    if (to && activeLink.contains(to)) return;
    scheduleHide();
  });

  window.addEventListener(
    "scroll",
    function () {
      if (activeLink) hide();
    },
    { passive: true }
  );
})();
