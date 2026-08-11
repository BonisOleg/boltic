(function () {
  "use strict";

  var form = document.querySelector(".checkout-form");
  if (!form) return;

  var PREFIX = "+380";
  var MAX_DIGITS = 9;

  var nameInput = form.querySelector("[data-validate-name]");
  var phoneInput = form.querySelector("[data-phone-mask]");
  var emailInput = form.querySelector("[data-validate-email]");

  function ensureErrorNode(input) {
    var field = input.closest(".field");
    if (!field) return null;
    var node = field.querySelector("[data-client-error]");
    if (!node) {
      node = document.createElement("div");
      node.className = "field-error";
      node.setAttribute("data-client-error", "1");
      field.appendChild(node);
    }
    return node;
  }

  function setError(input, message) {
    var node = ensureErrorNode(input);
    if (!node) return;
    if (message) {
      node.textContent = message;
      node.hidden = false;
      input.setAttribute("aria-invalid", "true");
    } else {
      node.textContent = "";
      node.hidden = true;
      input.removeAttribute("aria-invalid");
    }
  }

  function stripDigits(value) {
    return String(value || "").replace(/\d+/g, "");
  }

  function phoneDigits(value) {
    var digits = String(value || "").replace(/\D/g, "");
    if (digits.indexOf("380") === 0) digits = digits.slice(3);
    else if (digits.charAt(0) === "0" && digits.length >= 10) digits = digits.slice(1);
    return digits.slice(0, MAX_DIGITS);
  }

  function formatPhone(value) {
    return PREFIX + phoneDigits(value);
  }

  function caretInPrefix(input) {
    var start = input.selectionStart;
    return start !== null && start < PREFIX.length;
  }

  if (nameInput) {
    nameInput.addEventListener("beforeinput", function (e) {
      if (e.data && /\d/.test(e.data)) e.preventDefault();
    });
    nameInput.addEventListener("input", function () {
      var cleaned = stripDigits(nameInput.value);
      if (cleaned !== nameInput.value) nameInput.value = cleaned;
      if (nameInput.value.trim() && /\d/.test(nameInput.value)) {
        setError(nameInput, "ПІБ не може містити цифри");
      } else {
        setError(nameInput, "");
      }
    });
  }

  if (phoneInput) {
    phoneInput.value = formatPhone(phoneInput.value || PREFIX);

    phoneInput.addEventListener("keydown", function (e) {
      var start = phoneInput.selectionStart || 0;
      var end = phoneInput.selectionEnd || 0;
      var key = e.key;

      if (
        (key === "Backspace" && start <= PREFIX.length && end <= PREFIX.length) ||
        (key === "Backspace" && start < PREFIX.length) ||
        (key === "Delete" && start < PREFIX.length)
      ) {
        e.preventDefault();
        phoneInput.setSelectionRange(PREFIX.length, PREFIX.length);
        return;
      }

      if (
        key.length === 1 &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        !/^\d$/.test(key)
      ) {
        e.preventDefault();
      }

      if (
        /^\d$/.test(key) &&
        phoneDigits(phoneInput.value).length >= MAX_DIGITS &&
        start === end
      ) {
        e.preventDefault();
      }
    });

    phoneInput.addEventListener("input", function () {
      var digits = phoneDigits(phoneInput.value);
      phoneInput.value = PREFIX + digits;
      setError(
        phoneInput,
        digits.length === MAX_DIGITS
          ? ""
          : "Вкажіть повний номер: +380 і 9 цифр"
      );
    });

    phoneInput.addEventListener("focus", function () {
      phoneInput.value = formatPhone(phoneInput.value);
      if (caretInPrefix(phoneInput) || phoneInput.selectionStart === 0) {
        phoneInput.setSelectionRange(PREFIX.length, PREFIX.length);
      }
    });

    phoneInput.addEventListener("click", function () {
      if (caretInPrefix(phoneInput)) {
        phoneInput.setSelectionRange(PREFIX.length, PREFIX.length);
      }
    });

    phoneInput.addEventListener("paste", function (e) {
      e.preventDefault();
      var text = (e.clipboardData || window.clipboardData).getData("text");
      phoneInput.value = formatPhone(text);
      setError(
        phoneInput,
        phoneDigits(phoneInput.value).length === MAX_DIGITS
          ? ""
          : "Вкажіть повний номер: +380 і 9 цифр"
      );
    });
  }

  if (emailInput) {
    emailInput.addEventListener("blur", function () {
      var val = emailInput.value.trim();
      if (!val) {
        setError(emailInput, "");
        return;
      }
      if (!emailInput.checkValidity()) {
        setError(emailInput, "Вкажіть коректний email");
      } else {
        setError(emailInput, "");
      }
    });
    emailInput.addEventListener("input", function () {
      if (!emailInput.value.trim()) setError(emailInput, "");
    });
  }

  form.addEventListener("submit", function (e) {
    var ok = true;

    if (nameInput) {
      var name = nameInput.value.trim();
      if (!name) {
        setError(nameInput, "Вкажіть ПІБ");
        ok = false;
      } else if (/\d/.test(name)) {
        setError(nameInput, "ПІБ не може містити цифри");
        ok = false;
      } else {
        setError(nameInput, "");
      }
    }

    if (phoneInput) {
      phoneInput.value = formatPhone(phoneInput.value);
      if (phoneDigits(phoneInput.value).length !== MAX_DIGITS) {
        setError(phoneInput, "Вкажіть повний номер: +380 і 9 цифр");
        ok = false;
      } else {
        setError(phoneInput, "");
      }
    }

    if (emailInput) {
      var email = emailInput.value.trim();
      emailInput.value = email;
      if (email && !emailInput.checkValidity()) {
        setError(emailInput, "Вкажіть коректний email");
        ok = false;
      } else {
        setError(emailInput, "");
      }
    }

    if (!ok) e.preventDefault();
  });
})();
