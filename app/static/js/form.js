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
