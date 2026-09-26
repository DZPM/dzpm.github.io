"""Site plugin for davidarcos.net (theme "hst", Hic sunt trolls).

Three small things, kept together because they are all site specific:

1. EmbedExtension: a Markdown preprocessor. A line that is only a URL of a
   known provider becomes an embed; any other bare URL becomes a link.
2. Section and cover: every article gets `section` (from the front matter, or "portfolio" from 2012
   onward, "archive" before) and `cover_url`, derived, never stored.
3. Redirect stubs: for every article with an `original_url`, two stub pages
   are written at the WordPress addresses (with and without `/blog/`) that
   send the reader to the article; `redirect_from` adds more. The old date
   archives, the category, the pagination and the tag pages get stubs too.
   See docs/adr/0002.
4. Comments: content/comments/<slug>.json, produced once by the migration,
   attached to the article as `comments` (flat, oldest first).
5. Card covers: a 480 px copy of every cover in images/covers/, written into the
   output at build time (never committed) for the cards on the Home and the Blog,
   exposed as `cover_card_url`.
"""

import html
import json
import os
import re
from datetime import datetime
from urllib.parse import parse_qs, quote, unquote, urlparse

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from pelican import signals

PORTFOLIO_FROM = 2012
SECTIONS = ("portfolio", "archive", "notes")   # a Section: written in the front matter, or decided by the date
KINDS = {"charla": "🎤", "podcast": "🎙️", "entrevista": "💬", "mesa redonda": "👥", "artículo": "📝"}   # the Kind of a Portfolio post: one word and its emoji, on the card and at the top of the post

URL_LINE = re.compile(r"^\s*(https?://\S+)\s*$")
# The origin of every iframe embed_html can write, one per provider. It is the one list: embed_html builds its iframes
# from it, the page CSP takes its frame-src from it (EMBED_FRAME_SRC in pelicanconf.py), and tools/check_csp.py fails
# the build if a page frames an origin its CSP does not allow. To add a provider, add its origin here and its branch
# in embed_html.
EMBED_ORIGINS = {
    "youtube": "https://www.youtube-nocookie.com",
    "docs": "https://docs.google.com",
    "spotify": "https://open.spotify.com",
    "slideshare": "https://www.slideshare.net",
    "vimeo": "https://player.vimeo.com",
    "spreaker": "https://www.spreaker.com",
}


def embed_html(url):
    """Return the embed markup for a known provider URL, or None. The post text gives the URL: every value is escaped
    for the attribute or quoted for the path it goes into, so a quote in a URL cannot open a new attribute."""
    u = urlparse(url)
    url = html.escape(url, quote=True)
    host = u.netloc.lower().removeprefix("www.")
    qs = parse_qs(u.query)

    if host in ("youtube.com", "youtube-nocookie.com", "youtu.be"):
        if u.path == "/playlist" and qs.get("list"):
            return (
                f'<figure class="embed embed-video" data-url="{url}"><iframe loading="lazy" '
                f'src="{EMBED_ORIGINS["youtube"]}/embed/videoseries?list={quote(qs["list"][0], safe="")}" title="Lista de vídeos" '
                'allow="encrypted-media; picture-in-picture" allowfullscreen '
                'referrerpolicy="strict-origin-when-cross-origin"></iframe></figure>'
            )
        vid = qs.get("v", [None])[0] if host != "youtu.be" else u.path.strip("/")
        if not vid and u.path.startswith("/embed/"):
            vid = u.path.split("/")[2]
        if vid:
            return (
                f'<figure class="embed embed-video" data-url="{url}"><iframe loading="lazy" '
                f'src="{EMBED_ORIGINS["youtube"]}/embed/{quote(vid, safe="")}" title="Vídeo" '
                'allow="encrypted-media; picture-in-picture" allowfullscreen '
                'referrerpolicy="strict-origin-when-cross-origin"></iframe></figure>'
            )
    if host == "docs.google.com" and "/presentation/d/" in u.path:
        # published to the web (/d/e/<id>/pub) or shared with the link (/d/<id>/edit): both embed
        m = re.match(r"^(/presentation/d/(?:e/)?[^/]+)", u.path)
        if m:
            return (
                f'<figure class="embed embed-slides" data-url="{url}"><iframe loading="lazy" '
                f'src="{EMBED_ORIGINS["docs"]}{quote(m.group(1))}/embed?start=false&amp;loop=false&amp;delayms=3000" '
                'title="Presentación" allowfullscreen></iframe></figure>'
            )
    if host == "open.spotify.com" and u.path.startswith(("/episode/", "/show/")):
        return (
            f'<figure class="embed embed-audio embed-spotify" data-url="{url}"><iframe loading="lazy" '
            f'src="{EMBED_ORIGINS["spotify"]}/embed{quote(u.path)}" title="Podcast" allow="encrypted-media"></iframe></figure>'
        )
    if host == "slideshare.net" and "/embed_code/" in u.path:
        return (
            f'<figure class="embed embed-slides" data-url="{url}"><iframe loading="lazy" '
            f'src="{EMBED_ORIGINS["slideshare"]}{quote(u.path)}" title="Presentación" allowfullscreen></iframe></figure>'
        )
    if host in ("vimeo.com", "player.vimeo.com"):
        vid = u.path.rstrip("/").split("/")[-1]
        if vid.isdigit():
            return (
                f'<figure class="embed embed-video" data-url="{url}"><iframe loading="lazy" '
                f'src="{EMBED_ORIGINS["vimeo"]}/video/{quote(vid, safe="")}" title="Vídeo" allowfullscreen></iframe></figure>'
            )
    if host == "spreaker.com" and u.path.startswith("/embed/"):
        return (
            f'<figure class="embed embed-audio" data-url="{url}"><iframe loading="lazy" '
            f'src="{EMBED_ORIGINS["spreaker"]}{u.path}?{u.query.replace("&", "&amp;")}" title="Audio"></iframe></figure>'
        )
    return None


class EmbedPreprocessor(Preprocessor):
    def run(self, lines):
        out = []
        for line in lines:
            m = URL_LINE.match(line)
            if m:
                html = embed_html(m.group(1))
                out.append(html if html else f"<{m.group(1)}>")
            else:
                out.append(line)
        return out


class EmbedExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(EmbedPreprocessor(md), "hst_embeds", 25)


def makeExtension(**kwargs):
    return EmbedExtension(**kwargs)


# --- section and cover -------------------------------------------------------

IMG_RE = re.compile(r'(<a [^>]*>)?<img alt="([^"]*)" src="(?:\{static\})?(/(?:images|files)/[^"]+)">')


def sized_img(m, content_path, title=""):
    """A post image gets its size and lazy loading, and a link to itself unless it is already a link."""
    link, alt, src = m.group(1), m.group(2), m.group(3)
    path = os.path.join(content_path, src.lstrip("/"))
    if not os.path.exists(path):
        path = os.path.join(content_path, "extra", src.lstrip("/"))   # /files/ is served from content/extra/files/
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        return m.group(0)
    if not alt and title and src.startswith("/images/posts/"):
        alt = f"Foto de {title}"   # generic on purpose: the post around it is the description
    img = f'<img alt="{alt}" src="{src}" width="{w}" height="{h}" loading="lazy">'
    if link:
        # a link the post wrote itself: when it opens one of the site's own files (the full GIF, a bigger copy), it opens apart too
        if re.search(r'href="(?:\{static\})?/(?:images|files)/', link) and "target=" not in link:
            link = link[:-1] + ' target="_blank" rel="noopener">'
        return link + img
    return f'<a href="{src}" target="_blank" rel="noopener">{img}</a>'


YEAR_RE = re.compile(r"(?<![\d.,/:\-])\b((?:19[89]\d|20[0-2]\d))\b(?![\d.,:\-]\d|\s?(?:px|%|€|\$|MB|GB|KB|Mb|kb))")
SKIP_TAGS = ("a", "code", "pre", "span", "time", "h1", "h2", "h3", "figcaption", "svg")


# the tags a post's text links to on its first mention: proper nouns only (a company, a place, an event, a technology), never
# a common word (Personal, Fotos, Viajes...), which would link any sentence
LINKED_TAGS = {"Barcelona", "Bergen", "Blueliv", "Catchoom", "Data Science", "Django", "ESADE", "Erasmus", "EuroPython", "FOSDEM", "Flumotion",
               "GeeksHubs", "HIB", "Image Recognition", "Immfly", "L'Oasi", "Lead Ratings", "Madrid", "Menéame", "No cON Name", "PFC", "Pelican",
               "PyConES", "PyScript", "Python", "Python Barcelona", "Quantum Computing", "ScannerFM", "Stavanger", "Voss", "Wardley Maps", "WordPress"}


# the words a Portfolio post puts in bold on their first mention: what the post is about, never a name that is already a tag
# (those are linked instead, see LINKED_TAGS) and never a figure (those are the mono voice, see the num span)
KEYWORDS = ("deuda técnica", "sistemas distribuidos", "reconocimiento de imágenes", "entretenimiento a bordo", "computación cuántica",
            "mapas de Wardley", "problemas complejos", "buenas prácticas", "software libre", "código abierto", "microservicios",
            "escalabilidad", "rendimiento", "arquitectura", "seguridad", "estrategia", "complejidad", "streaming", "cloud", "SaaS")


def bold_keywords(html):
    """The first mention of each keyword in a Portfolio post becomes bold: what the post is about, stated once."""
    pending = list(KEYWORDS)
    def fn(text):
        claimed = []
        for w in list(pending):
            for m in re.finditer(r"(?<![\w'’])" + re.escape(w) + r"(?![\w'’])", text, re.I):
                if not any(s < m.end() and m.start() < e for s, e, _ in claimed):
                    claimed.append((m.start(), m.end(), w)); pending.remove(w); break
        out, i = [], 0
        for s, e, _ in sorted(claimed):
            out.append(text[i:s]); out.append(f"<strong>{text[s:e]}</strong>"); i = e
        out.append(text[i:])
        return "".join(out)
    return walk_text(html, fn)


def walk_text(html, fn):
    """Apply fn to every text node of html that is not inside a skipped element (a link, code, a heading, a span...)."""
    out, i, depth = [], 0, {t: 0 for t in SKIP_TAGS}
    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)[^>]*>", html):
        text = html[i:m.start()]
        out.append(text if any(depth.values()) else fn(text))
        closing, tag = m.group(1), m.group(2).lower()
        if tag in depth and not html[m.start():m.end()].endswith("/>"):
            depth[tag] = max(0, depth[tag] + (-1 if closing else 1))
        out.append(m.group(0))
        i = m.end()
    tail = html[i:]
    out.append(tail if any(depth.values()) else fn(tail))
    return "".join(out)


def link_tags(html, tags, site):
    """The first mention in the text of each of the post's own tags (the proper nouns of LINKED_TAGS) becomes a link to the
    tag's page: a post joins its era without a word of it being rewritten (docs/adr/0007: presentation, not text).
    Longer names first, so "Python Barcelona" is not cut by "Python"."""
    pending = sorted((t for t in tags if t.name in LINKED_TAGS), key=lambda t: -len(t.name))
    if not pending:
        return html
    def fn(text):
        claimed = []   # (start, end, tag): matched on the original text, never inside another match
        for t in list(pending):
            for m in re.finditer(r"(?<![\w'’])" + re.escape(t.name) + r"(?![\w'’])", text, re.I):
                if not any(s < m.end() and m.start() < e for s, e, _ in claimed):
                    claimed.append((m.start(), m.end(), t)); pending.remove(t); break
        out, i = [], 0
        for s, e, t in sorted(claimed):
            out.append(text[i:s]); out.append(f'<a class="tag-link" href="{site}/{t.url}" title="Etiqueta {t.name}">{text[s:e]}</a>'); i = e
        out.append(text[i:])
        return "".join(out)
    return walk_text(html, fn)


def mark_years(html):
    """Wrap the years in the text nodes of html in <span class="yr">, leaving the skipped elements alone."""
    out, i, depth = [], 0, {t: 0 for t in SKIP_TAGS}
    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)[^>]*>", html):
        text = html[i:m.start()]
        out.append(text if any(depth.values()) else YEAR_RE.sub(r'<span class="yr">\1</span>', text))
        closing, tag = m.group(1), m.group(2).lower()
        if tag in depth and not html[m.start():m.end()].endswith("/>"):
            depth[tag] = max(0, depth[tag] + (-1 if closing else 1))
        out.append(m.group(0))
        i = m.end()
    tail = html[i:]
    out.append(tail if any(depth.values()) else YEAR_RE.sub(r'<span class="yr">\1</span>', tail))
    return "".join(out)


NOTE_RE = re.compile(r"<p><em>((?:Imagen|Imágenes)\b[^<]*autor desconocido[^<]*|\((?:(?!</em>).)*\))</em></p>")   # a parenthetical note may hold a dead-link span   # a credit with a known author stays a plain italic line
_NOTE_ICON = {}
# a link to one of the author's networks gets that network's icon in front of its text, in any post or page
LINK_ICONS = {"linkedin.com": "linkedin", "github.com": "github", "stackoverflow.com": "stackoverflow", "x.com": "x", "twitter.com": "x",
              "instagram.com": "instagram", "flickr.com": "flickr", "youtube.com": "youtube", "youtu.be": "youtube", "slideshare.net": "slideshare", "keybase.io": "keybase", "pybcn.org": "pybcn"}
LINK_RE = re.compile(r'<a [^>]*href="https?://(?:www\.)?([^/"]+)[^"]*"[^>]*>(?!<(?:img|svg|iframe))')
_LINK_ICON = {}


def link_icons(html, settings):
    """Put the network's icon inside every link to LinkedIn, GitHub, X, YouTube and the rest, before its text."""
    def icon(name):
        if name == "pybcn":   # the one logo that is an image, not a mark drawn in the theme
            return '<span class="link-icon icon-pybcn"></span> '
        if name not in _LINK_ICON:
            with open(os.path.join(settings["THEME"], "templates", "icons", name + ".svg"), encoding="utf-8") as f:
                inner = re.sub(r"<title>.*?</title>|</?svg[^>]*>", "", f.read()).strip()
            _LINK_ICON[name] = f'<svg class="link-icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">{inner}</svg> '
        return _LINK_ICON[name]
    def sub(m):
        host = m.group(1).lower()
        name = next((v for k, v in LINK_ICONS.items() if host == k or host.endswith("." + k)), None)
        return m.group(0) + icon(name) if name else m.group(0)
    return LINK_RE.sub(sub, html)


def note_icon(settings):
    if "svg" not in _NOTE_ICON:
        with open(os.path.join(settings["THEME"], "templates", "icons", "note.svg"), encoding="utf-8") as f:
            _NOTE_ICON["svg"] = f.read().strip()
    return _NOTE_ICON["svg"]



# links other people wrote (inside archived comments and mentions) tell crawlers they are user content: rel gets
# nofollow and ugc, next to what it had. Only external http(s) links; mailto and bare anchors stay as they are
EXTERNAL_A = re.compile(r'<a\b([^>]*?\bhref="https?://(?!(?:www\.)?davidarcos\.net\b)[^"]*"[^>]*)>', re.I)


def ugc(text):
    def mark(m):
        attrs = m.group(1)
        rel = re.search(r'\brel="([^"]*)"', attrs)
        if not rel:
            return f'<a{attrs} rel="nofollow ugc">'
        tokens = rel.group(1).split()
        tokens += [t for t in ("nofollow", "ugc") if t not in tokens]
        return f'<a{attrs[:rel.start()]}rel="{" ".join(tokens)}"{attrs[rel.end():]}>'
    return EXTERNAL_A.sub(mark, text or "")

def decorate(content):
    body = content._content or ""   # a template page (search, 404, the map) has no content
    if "/images/" in body or "/files/" in body:
        # restored photos and other images: lazy, with their size so the page does not jump while they load
        title = re.sub(r"<[^>]+>", "", getattr(content, "title", "") or "").replace('"', "'")
        content._content = IMG_RE.sub(lambda m: sized_img(m, content.settings["PATH"], title), content._content)
    # a year mentioned in the running text gets the voice of the big ones (.yr): only in text, never inside a tag,
    # a link, code or an existing span, and only years the blog could talk about (1980 to 2029)
    if content._content and getattr(content, "date", None) is None and "stats." in content._content:
        content._content = fill_stats(content._content)   # a page states the site's figures; the build supplies them, before the years are marked
    if content._content:
        # a figure written in bold (**138**) is a number, not a shout: the mono voice, red, no weight. Bold stays for the names that matter
        content._content = re.sub(r"<strong>([\d][\d.,]*\s?(?:%|k|M)?)</strong>", r'<span class="num">\1</span>', content._content)
    if content._content:
        content._content = mark_years(content._content)
    # editorial notes: an italic aside in parentheses ("(Aquí había una encuesta...)") or a credit to nobody
    # ("Imagen: encontrada en la red, autor desconocido") becomes a banner, like the archive notice
    if content._content:
        content._content = link_icons(content._content, content.settings)
    if content._content:
        content._content = NOTE_RE.sub(lambda m: f'<aside class="banner note">{note_icon(content.settings)}<span>{m.group(1)}</span></aside>', content._content)
    date = getattr(content, "date", None)
    if date is None:
        return   # a page: nothing below applies
    if content._content and getattr(content, "tags", None):
        content._content = link_tags(content._content, content.tags, content.settings["SITEURL"])
    # every embed's title says which post it belongs to, so a list of frames reads as more than "Vídeo, Vídeo"
    ttl = re.sub(r"<[^>]+>", "", content.title or "").replace('"', "'")
    content._content = re.sub(r'(<iframe [^>]*title=")(Vídeo|Lista de vídeos|Presentación|Podcast|Audio)(")', lambda m: f"{m.group(1)}{m.group(2)}: {ttl}{m.group(3)}", content._content)
    # the Section: a `Section:` in the front matter wins (Notes, for short posts written new); otherwise the date decides
    content.section = getattr(content, "section", "") or ("portfolio" if date.year >= PORTFOLIO_FROM else "archive")
    if content.section == "portfolio" and content._content:
        content._content = bold_keywords(content._content)   # what the post is about, in bold, once (the Archive keeps its own emphasis)
    content.kind_emoji = KINDS.get(getattr(content, "kind", ""), "")
    content.kind_label = (getattr(content, "kind", "") or "").capitalize()   # "Charla", "Mesa redonda": the word before the date
    if content.section == "archive":
        content.kind_emoji, content.kind_label = "🗃️", "Archivado"   # an Archive post says so before its date, in brown
    elif content.section == "notes":
        content.kind_emoji, content.kind_label = "🗒️", "Nota"
    cover = getattr(content, "cover", "")
    site = content.settings["SITEURL"]
    # a Cover is a file in images/covers/, or, from a slash, any path on the site (a restored photo)
    content.cover_url = (f"{site}{cover}" if cover.startswith("/") else f"{site}/images/covers/{cover}") if cover else ""
    # the card copy exists only for the files in images/covers/ (write_card_covers makes them at the end of the build)
    content.cover_card_url = f"{site}/images/covers/card/{os.path.splitext(cover)[0]}.webp" if cover and not cover.startswith("/") else ""
    content.cover_width = 0
    if content.cover_card_url:
        try:
            from PIL import Image
            with Image.open(os.path.join(content.settings["PATH"], "images", "covers", cover)) as im:
                content.cover_width = im.width   # the real width, for the srcset descriptor
        except Exception:
            pass
    # what the post carries besides text, for the marks next to the comment count
    body = content._content
    content.media = {
        "fotos": len(re.findall(r'<img [^>]*src="/(?:images/posts|files)/', body)) + (1 if getattr(content, "cover", "") else 0),
        "vídeos": len(re.findall(r'<iframe [^>]*src="https://(?:www\.youtube-nocookie\.com|player\.vimeo\.com)/', body)),
        "presentaciones": len(re.findall(r'<iframe [^>]*src="https://(?:docs\.google\.com/presentation|www\.slideshare\.net)/', body)),
        "audios": len(re.findall(r'<iframe [^>]*src="https://(?:open\.spotify\.com|(?:www|widget)\.spreaker\.com)/', body)),
    }
    # for the card the blog index shows on hover: the first image of the body when there is no cover, and a short excerpt
    m = re.search(r'<img [^>]*src="(/(?:images/posts|files)/[^"]+)"', body)
    content.first_image = f"{site}{m.group(1)}" if m else ""
    # the caption's copy: a 480 px WebP of the first photo (write_card_covers makes it), so a list never loads a full photo
    content.first_image_card = f"{site}/images/posts/card/{m.group(1)[len('/images/posts/'):].rsplit('.', 1)[0]}.webp" if m and m.group(1).startswith("/images/posts/") else content.first_image
    _PEEK_PHOTOS.add(m.group(1)[len("/images/posts/"):]) if m and m.group(1).startswith("/images/posts/") else None
    cover = getattr(content, "cover", "")
    if cover.startswith("/images/posts/"):   # an Archive cover that is a restored photo: the same small copy
        content.cover_card_url = f"{site}/images/posts/card/{cover[len('/images/posts/'):].rsplit('.', 1)[0]}.webp"
        _PEEK_PHOTOS.add(cover[len("/images/posts/"):])
    # the pixel size of each picture the lists and the post show, for its width and height attributes: with no stylesheet
    # a page draws it at that size, not at the full width of the file, and with one the browser keeps its box before it loads
    base = content.settings["PATH"]
    source = lambda path: next((p for p in (base + path, os.path.join(base, "extra") + path) if os.path.isfile(p)), "")
    cover_file = (source(cover) if cover.startswith("/") else os.path.join(base, "images", "covers", cover)) if cover else ""
    content.cover_size = image_size(cover_file)
    content.card_size = image_size(cover_file, card=True) if content.cover_card_url else content.cover_size
    content.peek_size = content.card_size if cover else image_size(source(m.group(1)) if m else "", card=content.first_image_card != content.first_image)
    text = re.sub(r"<(figure|blockquote|pre|aside)\b[^>]*>.*?</\1>", " ", body, flags=re.S)
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))).strip()
    content.excerpt = text if len(text) <= 160 else text[:157].rsplit(" ", 1)[0] + "..."
    path = os.path.join(content.settings["PATH"], "comments", f"{content.slug}.json")
    content.comments = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            content.comments = json.load(f)
        for c in content.comments:
            c["html"] = ugc(mark_years(c["html"]))   # a year in a comment speaks like a year in the post
    # mentions: the pingbacks and trackbacks other sites sent, shown together as WordPress did
    path = os.path.join(content.settings["PATH"], "mentions", f"{content.slug}.json")
    content.mentions = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            content.mentions = json.load(f)
        for m in content.mentions:
            m["excerpt"] = ugc(mark_years(m.get("excerpt", "")))
    content.media["menciones"] = len(content.mentions)


# --- redirect stubs ----------------------------------------------------------

STUB = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={url}">
<meta name="robots" content="noindex">
</head>
<body>
<p>Esta página se ha movido a <a href="{url}">{url}</a>.</p>
</body>
</html>
"""


def stub_paths(original_url):
    """The two WordPress address shapes for a post: with and without /blog/."""
    path = unquote(urlparse(original_url).path).strip("/")
    if not path:
        return []
    paths = [path]
    if path.startswith("blog/"):
        paths.append(path[len("blog/"):])
    return paths


_ARTICLES = []
_PEEK_PHOTOS = set()   # the restored photos a list shows small: relative to images/posts/


def lint(generator):
    """The rules the README states, checked on every build: a Slug written by hand, a Summary and a Kind on every
    Portfolio post, a known Section, a Cover that exists, weighs under 300 KB and (a warning only) is at least 1700 px wide."""
    from PIL import Image
    covers = os.path.join(generator.settings["PATH"], "images", "covers")
    errors, narrow = [], []
    for a in generator.articles:
        if "slug" not in a.metadata:
            errors.append(f"{a.source_path}: no Slug")
        if a.section not in SECTIONS:
            errors.append(f"{a.slug}: Section {a.section!r} is not one of {', '.join(SECTIONS)}")
        if "section" in a.metadata and a.date.year < PORTFOLIO_FROM:
            errors.append(f"{a.slug}: an Archive post's Section is its date's, not the front matter's (docs/adr/0007)")
        if a.section == "portfolio" and not getattr(a, "summary", ""):
            errors.append(f"{a.slug}: a Portfolio post without a Summary")
        if a.section == "portfolio" and getattr(a, "kind", "") not in KINDS:
            errors.append(f"{a.slug}: a Portfolio post needs a Kind, one of {', '.join(KINDS)}")
        cover = getattr(a, "cover", "")
        if cover and not cover.startswith("/"):
            path = os.path.join(covers, cover)
            if not os.path.exists(path):
                errors.append(f"{a.slug}: cover {cover} does not exist")
                continue
            if os.path.getsize(path) > 300 * 1024:
                errors.append(f"{a.slug}: cover {cover} weighs {os.path.getsize(path) // 1024} KB, over 300")
            with Image.open(path) as im:
                if im.width < 1700:
                    narrow.append(f"{cover} ({im.width} px)")
    if narrow:
        print(f"covers under 1700 px wide, soft on a 2x screen: {len(narrow)}")
    if errors:
        raise SystemExit("post lint:\n  " + "\n  ".join(errors))


def stats(articles, settings):
    """The figures of the site, derived from the content on every build (never typed anywhere): what Sobre el blog,
    llms.txt and humans.txt state. Every figure comes from the same source the pages are built from."""
    text = lambda html: re.sub(r"<[^>]+>", " ", html or "")
    words = lambda html: len(re.findall(r"\S+", text(html)))
    portfolio = [a for a in articles if a.section == "portfolio"]
    archive = [a for a in articles if a.section == "archive"]
    comments = [c for a in articles for c in (getattr(a, "comments", None) or [])]
    mentions = [m for a in articles for m in (getattr(a, "mentions", None) or [])]
    by_year = {}
    for a in articles:
        by_year[a.date.year] = by_year.get(a.date.year, 0) + 1
    top_year = max(by_year, key=by_year.get)
    longest = max(articles, key=lambda a: words(a.content))
    most_commented = max(articles, key=lambda a: len(getattr(a, "comments", None) or []))
    # a restored photo: an image in the text, or an Archive cover that is one (a Cover given as a path)
    photos = [a for a in articles if re.search(r'<img [^>]*src="[^"]*/images/posts/', a.content or "") or getattr(a, "cover", "").startswith("/")]
    n_photos = sum(len(re.findall(r'<img [^>]*src="[^"]*/images/posts/', a.content or "")) + (1 if getattr(a, "cover", "").startswith("/") else 0) for a in articles)
    external = sum(len(re.findall(r'<a [^>]*href="https?://(?!davidarcos\.net)', a.content or "")) for a in articles)
    dead = sum(len(re.findall(r'<span class="dead-link', a.content or "")) for a in articles)
    meneame = [a for a in articles if getattr(a, "meneame_story", None)]
    return {
        "posts": len(articles), "portfolio": len(portfolio), "archive": len(archive),
        "top_year": top_year, "top_year_posts": by_year[top_year],
        "longest": longest, "longest_words": words(longest.content),
        "words": sum(words(a.content) for a in articles),
        "comment_words": sum(words(c.get("html", "")) for c in comments),
        "mention_words": sum(words(m.get("excerpt", "")) for m in mentions),
        "comments": len(comments), "people": len({c.get("avatar") for c in comments}),
        "most_commented": most_commented, "most_comments": len(most_commented.comments),
        "mentions": len(mentions), "dead_mentions": sum(1 for m in mentions if m.get("dead")),
        "tags": len({t.slug for a in articles for t in (getattr(a, "tags", None) or [])}),
        "photos": n_photos, "photo_posts": len(photos), "covers": sum(1 for a in articles if getattr(a, "cover", "")),
        "embeds": sum(len(re.findall(r"<iframe ", a.content or "")) for a in articles),
        "external": external + dead, "dead": dead,
        "meneame_posts": len(meneame), "meneos": sum(int(getattr(a, "meneame_meneos", 0) or 0) for a in meneame),
        "stubs": len(stub_plan(articles, settings)),
        "first_year": min(by_year),
        "comments_from": min(c["date"][:4] for c in comments), "comments_to": max(c["date"][:4] for c in comments),
        "longest_title": longest.title, "longest_url": f"/{longest.url}",
        "most_commented_title": most_commented.title, "most_commented_url": f"/{most_commented.url}",
    }


_STATS = {}
STAT_RE = re.compile(r"\{\{\s*stats\.(\w+)\s*\}\}")


def num_es(v):
    """1234 -> 1.234, the Spanish way; anything else as it is."""
    return f"{v:,}".replace(",", ".") if isinstance(v, int) else str(v)


def fill_stats(html):
    """{{ stats.posts }} in a page's text becomes the figure: the pages state the numbers, the build supplies them."""
    def sub(m):
        key = m.group(1)
        if key not in _STATS:
            raise SystemExit(f"stats: no figure called {key!r}")
        return str(_STATS[key]) if "year" in key or key.endswith(("_from", "_to")) else num_es(_STATS[key])   # a year is not a thousand
    return STAT_RE.sub(sub, html)


def remember_articles(generator):
    lint(generator)
    _ARTICLES[:] = list(generator.articles)
    generator.context["stats"] = s = stats(_ARTICLES, generator.settings)
    _STATS.clear(); _STATS.update(s)
    zero = [k for k, v in s.items() if isinstance(v, int) and v == 0]
    if zero:
        raise SystemExit(f"stats: these figures came out as zero, so something stopped counting: {', '.join(zero)}")
    # the neighbours, for the previous and next links at the end of a post (articles come newest first)
    for i, article in enumerate(_ARTICLES):
        article.next_article = _ARTICLES[i - 1] if i > 0 else None
        article.prev_article = _ARTICLES[i + 1] if i + 1 < len(_ARTICLES) else None


def write_stub(out, rel, title, url):
    directory = os.path.join(out, rel)
    path = os.path.join(directory, "index.html")
    if os.path.exists(path):
        raise SystemExit(f"redirect stub collides with existing output: {path}")
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(STUB.format(title=html.escape(title, quote=False), url=html.escape(url, quote=True)))   # a stub has no CSP: nothing in it goes out raw


def stub_plan(articles, settings):
    """Every redirect stub as (address, title, target): the old post addresses with and without /blog/,
    the WordPress date archives, the one category, the pagination, the old tag pages, and the settings' extras."""
    site = settings["SITEURL"]
    plan, dates, tags = [], set(), {}
    for article in articles:
        original = getattr(article, "original_url", None)
        if original:
            target = f"{site}/{article.url}"
            rels = stub_paths(original)
            extra = getattr(article, "redirect_from", "")
            rels += [r.strip().strip("/") for r in extra.split(",") if r.strip()]
            plan += [(rel, article.title, target) for rel in rels]
        d = article.date
        dates.update({f"blog/{d:%Y}", f"blog/{d:%Y/%m}", f"blog/{d:%Y/%m/%d}"})
        for tag in getattr(article, "tags", []) or []:
            tags[tag.slug] = tag
    blog = f"{site}/blog/"
    plan += [(rel, "Blog", blog) for rel in sorted(dates)]
    plan.append(("blog/category/uncategorized", "Blog", blog))
    plan += [(f"blog/page/{page}", "Blog", blog) for page in range(2, 20)]
    plan += [(f"blog/tag/{slug}", tag.name, f"{site}/{tag.url}") for slug, tag in tags.items()]
    # old addresses that still get readers but whose post is not on the site: to the blog index
    plan += [(rel.strip("/"), "Blog", blog) for rel in settings.get("REDIRECTS_TO_BLOG", [])]
    plan += [(rel.strip("/"), title, f"{site}/{target}") for rel, (title, target) in settings.get("REDIRECTS", {}).items()]
    return plan


def write_stubs(pelican):
    # Runs after every regular page is written, so a stub landing on an
    # existing output file is detected instead of silently overwritten.
    plan = stub_plan(_ARTICLES, pelican.settings)
    for rel, title, target in plan:
        write_stub(pelican.output_path, rel, title, target)
    print(f"redirect stubs: {len(plan)}")


# --- card covers ------------------------------------------------------------

CARD_WIDTH = 480


def style_feed(pelican):
    """The feed gets a stylesheet instruction, so a browser shows a page instead of raw XML (theme/feed.xsl); readers ignore it.
    The XSL and the stylesheet it loads carry the asset version, like every other file under /theme/, so a long cache is safe."""
    v = pelican.settings.get("ASSET_VERSION", "dev")
    xsl = os.path.join(pelican.output_path, "theme", "feed.xsl")
    if os.path.isfile(xsl):
        with open(xsl, encoding="utf-8") as f:
            text = f.read()
        with open(xsl, "w", encoding="utf-8") as f:
            f.write(text.replace('href="/theme/css/style.css"', f'href="/theme/css/style.css?v={v}"'))
    path = os.path.join(pelican.output_path, pelican.settings.get("FEED_ATOM", "") or "")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        xml = f.read()
    head = '<?xml version="1.0" encoding="utf-8"?>'
    if xml.startswith(head) and "xml-stylesheet" not in xml:
        xml = head + f'\n<?xml-stylesheet type="text/xsl" href="{pelican.settings["SITEURL"]}/theme/feed.xsl?v={v}"?>' + xml[len(head):]
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)


def version_theme_urls(pelican):
    """The fonts and images the stylesheet loads get the same content hash the templates give them (ASSET_HASH), so the
    preloaded font and the one the stylesheet asks for are one address, and one download. A file with no hash stops the build."""
    css = os.path.join(pelican.output_path, "theme", "css", "style.css")
    if not os.path.isfile(css):
        return
    hashes = pelican.settings["ASSET_HASH"]

    def versioned(m):
        key = f"{m.group(1)}/{m.group(2)}"
        if key not in hashes:
            raise RuntimeError(f"style.css loads {key}, which has no ASSET_HASH entry")
        return f'url("../{key}?v={hashes[key]}")'

    with open(css, encoding="utf-8") as f:
        text = f.read()
    with open(css, "w", encoding="utf-8") as f:
        f.write(re.sub(r'url\("\.\./(fonts|img)/([^"?]+)"\)', versioned, text))


_SIZES = {}


def image_size(path, card=False):
    """(width, height) of an image file, or of its card copy (at most CARD_WIDTH wide, as write_card_covers makes it).
    (0, 0) when there is no file, and then the template writes no attributes."""
    if (path, card) not in _SIZES:
        try:
            from PIL import Image
            with Image.open(path) as im:
                w, h = im.size
            if card and w > CARD_WIDTH:
                w, h = CARD_WIDTH, round(h * CARD_WIDTH / w)
            _SIZES[(path, card)] = (w, h)
        except (OSError, ValueError):
            _SIZES[(path, card)] = (0, 0)
    return _SIZES[(path, card)]


def write_card_covers(pelican):
    """A 480 px wide WebP copy of every cover, for the cards: the originals stay for the post and for sharing."""
    from PIL import Image
    src_dir = os.path.join(pelican.settings["PATH"], "images", "covers")
    out_dir = os.path.join(pelican.output_path, "images", "covers", "card")
    if not os.path.isdir(src_dir):
        return
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(src_dir)):
        src = os.path.join(src_dir, name)
        if not os.path.isfile(src):
            continue
        with Image.open(src) as im:
            im = im.convert("RGB")
            if im.width > CARD_WIDTH:
                im = im.resize((CARD_WIDTH, round(im.height * CARD_WIDTH / im.width)), Image.LANCZOS)
            im.save(os.path.join(out_dir, os.path.splitext(name)[0] + ".webp"), "WEBP", quality=75, method=6)
        n += 1
    # the restored photos the lists show in their captions: the same small copy, under images/posts/card/
    photos_dir = os.path.join(pelican.settings["PATH"], "images", "posts")
    for rel in sorted(_PEEK_PHOTOS):
        src = os.path.join(photos_dir, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(pelican.output_path, "images", "posts", "card", os.path.splitext(rel)[0] + ".webp")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with Image.open(src) as im:
            im = im.convert("RGB")
            if im.width > CARD_WIDTH:
                im = im.resize((CARD_WIDTH, round(im.height * CARD_WIDTH / im.width)), Image.LANCZOS)
            im.save(dst, "WEBP", quality=75, method=6)
        n += 1
    print(f"card covers and caption photos: {n}")


def register():
    signals.content_object_init.connect(decorate)
    signals.article_generator_finalized.connect(remember_articles)
    signals.finalized.connect(write_stubs)
    signals.finalized.connect(style_feed)
    signals.finalized.connect(version_theme_urls)
    signals.finalized.connect(write_card_covers)
