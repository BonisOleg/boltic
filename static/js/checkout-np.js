(function () {
  "use strict";

  var root = document.querySelector("[data-checkout-delivery]");
  if (!root) return;

  var cfg = {
    npCitiesUrl: root.getAttribute("data-np-cities-url") || "",
    npWarehousesUrl: root.getAttribute("data-np-warehouses-url") || "",
    npConfigured: root.getAttribute("data-np-configured") === "true",
  };

  var npBlock = root.querySelector("[data-np-block]");
  var methodInputs = root.querySelectorAll('input[name="shipping_method"]');
  var typeInputs = root.querySelectorAll('input[name="np_delivery_type"]');
  var cityWrap = root.querySelector("[data-np-city]");
  var whWrap = root.querySelector("[data-np-warehouse]");
  var cityInput = cityWrap && cityWrap.querySelector('input[name="np_city"]');
  var cityRef = cityWrap && cityWrap.querySelector('input[name="np_city_ref"]');
  var cityList = cityWrap && cityWrap.querySelector("[data-np-list]");
  var whInput = whWrap && whWrap.querySelector('input[name="np_warehouse"]');
  var whRef = whWrap && whWrap.querySelector('input[name="np_warehouse_ref"]');
  var whList = whWrap && whWrap.querySelector("[data-np-list]");

  var errorEl = root.querySelector("[data-np-error]");
  var cityTimer = null;
  var whTimer = null;
  var abortCity = null;
  var abortWh = null;

  function showNpError(msg) {
    if (!errorEl) return;
    errorEl.textContent = msg || "";
    errorEl.hidden = !msg;
  }

  function clearNpError() {
    showNpError("");
  }

  function selectedMethod() {
    var el = root.querySelector('input[name="shipping_method"]:checked');
    return el ? el.value : "";
  }

  function selectedType() {
    var el = root.querySelector('input[name="np_delivery_type"]:checked');
    return el ? el.value : "warehouse";
  }

  function syncMethod() {
    var isNp = selectedMethod() === "nova_poshta";
    if (npBlock) npBlock.hidden = !isNp;
    if (!isNp) {
      hideList(cityList);
      hideList(whList);
    } else if (cityRef && cityRef.value && whInput) {
      whInput.disabled = false;
    }
  }

  function hideList(list) {
    if (!list) return;
    list.hidden = true;
    list.innerHTML = "";
  }

  function renderList(list, items, onPick) {
    if (!list) return;
    list.innerHTML = "";
    if (!items.length) {
      var empty = document.createElement("li");
      empty.className = "np-suggest__empty";
      empty.textContent = "Нічого не знайдено";
      list.appendChild(empty);
      list.hidden = false;
      return;
    }
    items.forEach(function (item) {
      var li = document.createElement("li");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "np-suggest__item";
      btn.textContent = item.name;
      btn.addEventListener("click", function () {
        onPick(item);
        hideList(list);
      });
      li.appendChild(btn);
      list.appendChild(li);
    });
    list.hidden = false;
  }

  function fetchJson(url, signal) {
    return fetch(url, {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
      signal: signal,
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok || data.ok === false) {
          throw new Error((data && data.error) || "Помилка запиту");
        }
        return data.items || [];
      });
    });
  }

  function searchCities(q) {
    if (!cfg.npCitiesUrl || q.trim().length < 2) {
      hideList(cityList);
      return;
    }
    if (abortCity) abortCity.abort();
    abortCity = new AbortController();
    clearNpError();
    fetchJson(
      cfg.npCitiesUrl + "?q=" + encodeURIComponent(q.trim()),
      abortCity.signal
    )
      .then(function (items) {
        renderList(cityList, items, function (item) {
          cityInput.value = item.name;
          cityRef.value = item.ref;
          whInput.value = "";
          whRef.value = "";
          whInput.disabled = false;
          whInput.focus();
        });
      })
      .catch(function (err) {
        if (err.name === "AbortError") return;
        hideList(cityList);
        showNpError(err.message || "Не вдалося завантажити міста");
      });
  }

  function searchWarehouses(q) {
    if (!cfg.npWarehousesUrl || !cityRef || !cityRef.value) {
      hideList(whList);
      return;
    }
    if (abortWh) abortWh.abort();
    abortWh = new AbortController();
    var url =
      cfg.npWarehousesUrl +
      "?city_ref=" +
      encodeURIComponent(cityRef.value) +
      "&type=" +
      encodeURIComponent(selectedType()) +
      "&q=" +
      encodeURIComponent(q.trim());
    clearNpError();
    fetchJson(url, abortWh.signal)
      .then(function (items) {
        renderList(whList, items, function (item) {
          whInput.value = item.name;
          whRef.value = item.ref;
        });
      })
      .catch(function (err) {
        if (err.name === "AbortError") return;
        hideList(whList);
        showNpError(err.message || "Не вдалося завантажити відділення");
      });
  }

  methodInputs.forEach(function (input) {
    input.addEventListener("change", syncMethod);
  });

  typeInputs.forEach(function (input) {
    input.addEventListener("change", function () {
      if (whInput) {
        whInput.value = "";
        whRef.value = "";
      }
      hideList(whList);
      if (cityRef && cityRef.value) searchWarehouses("");
    });
  });

  if (cityInput) {
    cityInput.addEventListener("input", function () {
      cityRef.value = "";
      whInput.value = "";
      whRef.value = "";
      whInput.disabled = true;
      clearTimeout(cityTimer);
      cityTimer = setTimeout(function () {
        searchCities(cityInput.value);
      }, 280);
    });
    cityInput.addEventListener("focus", function () {
      if (cityInput.value.trim().length >= 2 && !cityRef.value) {
        searchCities(cityInput.value);
      }
    });
  }

  if (whInput) {
    whInput.addEventListener("input", function () {
      whRef.value = "";
      clearTimeout(whTimer);
      whTimer = setTimeout(function () {
        searchWarehouses(whInput.value);
      }, 280);
    });
    whInput.addEventListener("focus", function () {
      if (cityRef && cityRef.value) searchWarehouses(whInput.value || "");
    });
  }

  document.addEventListener("click", function (e) {
    if (cityWrap && !cityWrap.contains(e.target)) hideList(cityList);
    if (whWrap && !whWrap.contains(e.target)) hideList(whList);
  });

  syncMethod();
  if (cityRef && cityRef.value && whInput) whInput.disabled = false;
})();
