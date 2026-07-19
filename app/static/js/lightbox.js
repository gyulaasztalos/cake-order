// Gallery lightbox: click a thumbnail to view the full-size photo in an
// overlay, with prev/next navigation, keyboard control, and focus restore.
// No inline handlers — the app's strict CSP forbids them.
(function () {
  "use strict";

  const overlay = document.getElementById("co-lightbox");
  const image = document.getElementById("co-lightbox-img");
  if (!overlay || !image) return;

  // Every clickable thumbnail on the page, in DOM order == display order.
  const items = Array.from(document.querySelectorAll("[data-lightbox] .co-gallery-item"));
  if (items.length === 0) return;

  let index = 0;
  let lastFocus = null;

  function show(i) {
    index = (i + items.length) % items.length; // wrap around
    const full = items[index].getAttribute("data-full");
    if (full) image.src = full;
  }

  function open(i) {
    lastFocus = document.activeElement;
    show(i);
    overlay.hidden = false;
    document.body.classList.add("co-lightbox-open");
    // Focus the overlay so Escape/arrow keys are captured immediately.
    overlay.focus();
  }

  function close() {
    overlay.hidden = true;
    image.removeAttribute("src");
    document.body.classList.remove("co-lightbox-open");
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
  }

  items.forEach(function (item, i) {
    item.addEventListener("click", function () {
      open(i);
    });
  });

  overlay.addEventListener("click", function (event) {
    const action = event.target.closest("[data-lb-prev], [data-lb-next], [data-lb-close]");
    if (action) {
      if (action.hasAttribute("data-lb-prev")) show(index - 1);
      else if (action.hasAttribute("data-lb-next")) show(index + 1);
      else close();
      return;
    }
    // A click on the backdrop itself (not the image) closes the viewer.
    if (event.target === overlay) close();
  });

  document.addEventListener("keydown", function (event) {
    if (overlay.hidden) return;
    if (event.key === "Escape") close();
    else if (event.key === "ArrowLeft") show(index - 1);
    else if (event.key === "ArrowRight") show(index + 1);
  });
})();
