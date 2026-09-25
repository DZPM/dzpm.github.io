---
status: accepted
---
# No first party JavaScript that a page depends on

Post pages, the Blog and the Home depend on no script of their own: with JavaScript off they read, navigate and look the same. Embeds are plain iframes whose scripts run inside the frame, the Badge and the Banner are HTML, and the theme follows the reader's browser through `light-dark()` in CSS. The only pages that need a script are Search and the Not found page, which run Pagefind.

One script does load on every page: `theme/js/theme.js`, a few dozen lines, in `<head>` so a saved theme never flashes the other ground. It does two things and talks to nothing: it reads one `localStorage` key and sets `data-theme` on `<html>` (the theme switch), and it sets a class on `<html>` once the page has scrolled (the header folds into one row); the CSS does the rest. Without it the switch is hidden, the page follows the browser and the header stays open. That is the line the rule draws: a script may enhance a page, never carry it, and never call out.

The rule exists because every feature that erodes it (lazy embed facades, analytics, share buttons, a comment widget) is cheap to add and expensive to keep, and because a page with no script it depends on has nothing to maintain, nothing to break, and nothing to leak.

## Consequences

- Every page carries a Content-Security-Policy in a `<meta>` element (GitHub Pages sends no headers): no inline script or style anywhere, scripts and images only from the site, frames only from the embed providers. The scripts are files: `theme/js/theme.js` on every page and `theme/js/search.js` on the Search and the Not found pages; Pagefind's WebAssembly needs `'wasm-unsafe-eval'`. Structured data is microdata in the HTML, not JSON-LD, because JSON-LD is a `<script>` element.
- Cloudflare features that inject or rewrite HTML (Rocket Loader, Email Address Obfuscation, Auto Minify, Automatic HTTPS Rewrites, Web Analytics automatic setup) must stay off (the list is in `docs/edge.md`), and the post cutover check asserts a Post contains no `<script>` other than `theme.js` and no `cdn-cgi` reference.
- If analytics are ever wanted, Cloudflare zone analytics is the only option, since it is server side.
