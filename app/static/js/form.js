// Live character counter for the description field. Progressive enhancement
// only — the maxlength attribute and the server enforce the real limit.
(function () {
  "use strict";
  var area = document.querySelector("textarea[data-counter]");
  if (!area) return;
  var out = document.getElementById(area.dataset.counter);
  if (!out) return;
  var max = parseInt(area.getAttribute("maxlength"), 10);
  var update = function () {
    out.textContent = "(" + area.value.length + " / " + max + ")";
  };
  area.addEventListener("input", update);
  update();
})();

// Slice count is required for the per-slice cake types (birthday/kids/wedding/
// shaped) and optional for Desszertek/Egyéb. Keep the `required` attribute and
// the */"nem kötelező" markers in sync with the chosen type. Progressive
// enhancement only — orders.validate() enforces the rule server-side.
(function () {
  "use strict";
  var portions = document.getElementById("portions");
  var type = document.getElementById("cake_type");
  if (!portions || !type) return;
  var required = (portions.dataset.portionsRequiredTypes || "").split(",").filter(Boolean);
  var star = document.querySelector("[data-portions-req]");
  var opt = document.querySelector("[data-portions-opt]");
  var sync = function () {
    var need = required.indexOf(type.value) !== -1;
    portions.required = need;
    if (star) star.hidden = !need;
    if (opt) opt.hidden = need;
  };
  type.addEventListener("change", sync);
  sync();
})();
