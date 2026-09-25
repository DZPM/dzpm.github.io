// The theme switch. Runs in <head>, before the first paint, so a saved choice never flashes the other ground.
// By default the page follows the browser; a click flips it and keeps the choice in localStorage under "theme".
// A choice that matches the browser again is forgotten, so the page goes back to following it.
(function () {
  var root = document.documentElement;
  var metas = document.querySelectorAll('meta[name="theme-color"]');   // the browser chrome follows the choice too
  function system() { return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"; }
  function current() {
    try { var t = localStorage.getItem("theme"); return t === "light" || t === "dark" ? t : system(); } catch (e) { return system(); }
  }
  function apply(theme) {
    root.setAttribute("data-theme", theme);
    for (var i = 0; i < metas.length; i++) metas[i].content = theme === "dark" ? "#161615" : "#e8e6e0";
    var button = document.querySelector(".theme-switch");
    if (button) {
      var label = theme === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
      button.setAttribute("aria-label", label);
      button.title = label;
    }
  }
  apply(current());
  document.addEventListener("DOMContentLoaded", function () {
    var button = document.querySelector(".theme-switch");
    if (!button) return;
    button.hidden = false;   // the HTML hides it: with no script the button does nothing, and the page follows the browser
    apply(root.getAttribute("data-theme"));
    button.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      try { next === system() ? localStorage.removeItem("theme") : localStorage.setItem("theme", next); } catch (e) {}
      apply(next);
    });
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () { apply(current()); });
  // the header: measured once (the spacer keeps its place while it is fixed), then folded into one row
  // once the page has scrolled past the sentinel (CSS does the folding)
  document.addEventListener("DOMContentLoaded", function () {
    var header = document.querySelector(".site-header"), sentinel = document.querySelector(".scroll-sentinel");
    if (!header || !sentinel || !("IntersectionObserver" in window)) return;
    function measure() {
      var folded = root.classList.contains("is-scrolled");
      root.classList.remove("is-scrolled");
      root.style.setProperty("--header-h", header.offsetHeight + "px");
      if (folded) root.classList.add("is-scrolled");
    }
    // DOMContentLoaded can fire before the stylesheet has been applied (no script follows it), and an unstyled header is
    // four times taller: measure once everything has loaded, and again when the fonts are in and on every resize
    addEventListener("load", function () { measure(); root.classList.add("js-header"); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { if (root.classList.contains("js-header")) measure(); });
    addEventListener("resize", measure);
    new IntersectionObserver(function (entries) {
      root.classList.toggle("is-scrolled", !entries[0].isIntersecting);
    }).observe(sentinel);
  });
})();
