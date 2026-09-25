// Pagefind search, shared by /blog/buscar/ and the 404 page: one file, loaded by absolute path
// because the 404 page is served at any depth. The body's data-search says which page runs it.
const SITE = "{{ SITEURL }}";
const form = document.getElementById("search-form");
const input = document.getElementById("q");
const status = document.getElementById("search-status");
const list = document.getElementById("search-results");
const icon = id => `<svg class="mark-icon" width="14" height="14" aria-hidden="true"><use href="#i-${id}"/></svg>`;
const ICONS = {
  meneos: '<span class="mark-icon mark-icon-meneame" aria-hidden="true"></span>',
  comentarios: icon("comment"),
  fotos: icon("photo"),
  videos: icon("video"),
  presentaciones: icon("slides"),
  audios: icon("audio"),
  menciones: icon("mention"),
};
const ONE = { meneos: "meneo", comentarios: "comentario", fotos: "foto", videos: "vídeo", presentaciones: "presentación", audios: "audio", menciones: "mención" };
const WORD = { videos: "vídeos" };
function marks(meta, full) {
  const wrap = document.createElement("span");
  wrap.className = full ? "marks-window" : "year-item-marks";
  if (full) wrap.setAttribute("aria-hidden", "true");
  for (const kind of Object.keys(ICONS)) {
    const n = Number(meta[kind] || 0);
    if (!n) continue;
    const word = n === 1 ? ONE[kind] : (WORD[kind] || kind);
    const m = document.createElement("span");
    m.className = "mark mark-" + (kind === "meneos" ? "meneame" : kind === "comentarios" ? "comments" : "media");
    m.title = n + " " + word;
    m.innerHTML = ICONS[kind] + " " + n + (full ? '<span class="mark-word"> ' + word + "</span>" : "");
    wrap.append(m);
  }
  return wrap.childElementCount ? wrap : null;
}
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
function fechaEs(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || "");
  return m ? `${Number(m[3])} de ${MESES[Number(m[2]) - 1]} de ${m[1]}` : "";
}

async function runSearch(params) {
  const q = (params.get("q") || "").trim();
  const tag = (params.get("tag") || "").trim();
  if (input && q) input.value = q;
  if (!q && !tag) return;
  status.textContent = "Buscando...";
  let pagefind;
  try {
    pagefind = await import(SITE + "/pagefind/pagefind.js");
    await pagefind.init();
  } catch (e) {
    status.textContent = "La búsqueda no está disponible.";
    return;
  }
  const options = { sort: { date: "desc" } };
  if (tag) options.filters = { tag: tag };
  const search = await pagefind.search(q || null, options);
  const results = await Promise.all(search.results.slice(0, 50).map(r => r.data()));
  list.replaceChildren();
  if (!results.length) {
    status.textContent = tag ? `Nada con la etiqueta "${tag}".` : `Nada para "${q}".`;
    return;
  }
  status.textContent = tag
    ? `${results.length} ${results.length === 1 ? "entrada" : "entradas"} con la etiqueta "${tag}"`
    : `${results.length} ${results.length === 1 ? "resultado" : "resultados"} para "${q}"`;
  for (const r of results) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = r.url;
    a.textContent = r.meta.title || r.url;
    // the same line as a post and a row: what it is, then the date, in the era's colour
    const kind = document.createElement("span");
    kind.className = "search-kind";
    kind.innerHTML = '<span aria-hidden="true">' + (r.meta.emoji || "") + "</span> " + (r.meta.clase || "") + ' <span class="card-del">del</span>';
    const when = document.createElement("time");
    when.dateTime = (r.meta.date || "").slice(0, 10);
    when.textContent = fechaEs(r.meta.date);
    if (r.meta.seccion === "archive") li.classList.add("is-archive");
    const p = document.createElement("p");
    // the excerpt is a window into the text: say so at both ends when it does not start or end a sentence
    const text = r.excerpt.replace(/<[^>]+>/g, "").trim();
    const head = /^[A-ZÁÉÍÓÚÑ¿¡"(]/.test(text) ? "" : "(...) ";
    const tail = /[.!?")]$/.test(text) ? "" : " (...)";
    p.innerHTML = head + r.excerpt + tail;
    if (tag && !q) {
      // a tag search has no query term: mark the tag's name where the excerpt says it
      const re = new RegExp("(" + tag.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
      for (const node of Array.from(p.childNodes)) {
        if (node.nodeType !== Node.TEXT_NODE || !re.test(node.textContent)) continue;
        const span = document.createElement("span");
        span.innerHTML = node.textContent.replace(/[&<>]/g, ch => ({"&": "&amp;", "<": "&lt;", ">": "&gt;"}[ch])).replace(re, "<mark>$1</mark>");
        node.replaceWith(...span.childNodes);
      }
    }
    if (r.meta.clase) li.append(kind, " ");
    li.append(when, " ", a);
    const mk = marks(r.meta, false);
    if (mk) li.append(mk, marks(r.meta, true));
    li.append(p);
    list.append(li);
  }
}
if (form) form.addEventListener("submit", ev => {
  ev.preventDefault();
  const params = new URLSearchParams({ q: input.value });
  history.replaceState(null, "", location.pathname + "?" + params);
  runSearch(params);
});

if (document.body.dataset.search === "404") {
  // Turn the missing path into a query: /blog/tag/python/ is a tag search,
  // /blog/2007/11/09/free-krusher/ searches the words of the slug.
  const parts = location.pathname.split("/").filter(Boolean);
  const params = new URLSearchParams();
  const tagAt = parts.indexOf("tag");
  if (tagAt >= 0 && parts[tagAt + 1]) {
    params.set("tag", decodeURIComponent(parts[tagAt + 1]).replace(/-/g, " "));
  } else {
    const words = parts.filter(p => !/^\d+$/.test(p) && p !== "blog").join(" ").replace(/[-_.]+/g, " ");
    if (words) params.set("q", decodeURIComponent(words));
  }
  runSearch(params);
} else {
  runSearch(new URLSearchParams(location.search));
}
