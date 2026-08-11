/* Автоприбирання htmx-підказок біля кнопок дій. */
(function () {
  "use strict";

  var VISIBLE_MS = 2600;
  var FADE_MS = 260;

  function scheduleHide(slot) {
    var note = slot.querySelector("[data-note-life]");
    if (!note) {
      return;
    }
    if (slot._noteTimers) {
      slot._noteTimers.forEach(clearTimeout);
    }
    slot._noteTimers = [
      setTimeout(function () {
        note.classList.add("is-leaving");
      }, VISIBLE_MS),
      setTimeout(function () {
        if (note.parentNode === slot) {
          slot.replaceChildren();
        }
      }, VISIBLE_MS + FADE_MS),
    ];
  }

  document.body.addEventListener("htmx:afterSwap", function (event) {
    var slot = event.target;
    if (slot && slot.hasAttribute && slot.hasAttribute("data-action-note")) {
      scheduleHide(slot);
    }
  });
})();
