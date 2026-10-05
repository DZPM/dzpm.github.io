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
6. Share cards: a 1200x630 image for every post and page (not the home, which has
   og.png), drawn at build time and never committed: what a shared link shows.
   Exposed as `og_image`, `og_image_type` and `og_image_alt`. See docs/adr/0011.
7. Drafts: a post with `Status: draft` builds locally at /borradores/<slug>/ with its cover
   and cards. In production (DRAFT_SAVE_AS empty) nothing of it reaches the output: no card
   is drawn for it, and the image files only it uses are removed after Pelican copies them.
"""

import hashlib
import html
import json
import os
import re
import subprocess
from datetime import datetime
from urllib.parse import parse_qs, quote, unquote, urlparse

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from pelican import signals
from pelican.urlwrappers import Category

PORTFOLIO_FROM = 2012
SECTIONS = ("portfolio", "archive", "notes")   # a Section: written in the front matter, or decided by the date
KINDS = {"charla": "🎤", "podcast": "🎙️", "entrevista": "💬", "mesa redonda": "👥", "artículo": "📝"}   # the Kind of a Portfolio post: one word and its emoji, on the card and at the top of the post

URL_LINE = re.compile(r"^\s*(https?://\S+)\s*$")
# A media note: a line in the place of an embed, for a video or an audio that is not there. "Pendiente:" when its owner
# has not published it yet, "Retirado:" when its owner took it down. The line names what it is and whose it is:
#   Pendiente: el vídeo de la charla, en [el YouTube de CPS Spain](https://www.youtube.com/@cpsspain).
#   Retirado: el audio de la entrevista, en [el Spreaker de Scanner FM](https://www.spreaker.com/...).
# The link goes to the owner's channel (pending) or is the dead address, shown as a dead link (removed).
MEDIA_NOTE_LINE = re.compile(r"^\s*(Pendiente|Retirado):\s*(.+?),\s*en\s*\[([^\]]+)\]\((https?://[^)\s]+)\)\.?\s*$")
MEDIA_NOTE_ICON = (
    '<svg class="banner-icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/>'
    '<path d="M10 9l5 3-5 3z" fill="currentColor" stroke="none"/></svg>'
)
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


def media_note_html(state, what, owner, url):
    """Return the banner for a media note (see MEDIA_NOTE_LINE). Every value comes from the post text and is escaped."""
    what, owner, url = (html.escape(v, quote=True) for v in (what, owner, url))
    if state == "Pendiente":
        first, second = f"Aquí irá {what}.", f'Lo añadiré cuando se publique en <a href="{url}" rel="noopener">{owner}</a>.'
    else:
        owner = owner[:1].upper() + owner[1:]   # it starts the sentence
        first, second = f"Aquí había {what}.", f'<span class="dead-link" title="Enlace roto: {url}">{owner}</span> ya no existe.'
    text = f"<span>{first}</span><br><span>{second}</span>"   # two lines; the stylesheet puts a gap between them, the br keeps them apart without it
    return (
        f'<aside class="banner media-note media-{"pending" if state == "Pendiente" else "removed"}" data-pagefind-ignore>'
        f"{MEDIA_NOTE_ICON}<span>{text}</span></aside>"
    )


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
            n = MEDIA_NOTE_LINE.match(line)
            if m:
                html = embed_html(m.group(1))
                out.append(html if html else f"<{m.group(1)}>")
            elif n:
                out.append(media_note_html(*n.groups()))
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
              "instagram.com": "instagram", "flickr.com": "flickr", "youtube.com": "youtube", "youtu.be": "youtube", "vimeo.com": "vimeo", "slideshare.net": "slideshare", "keybase.io": "keybase", "pybcn.org": "pybcn",
              "wikipedia.org": "wikipedia", "archive.org": "internetarchive", "docs.google.com": "googleslides",   # every docs.google.com link here is a deck
              "meneame.net": "meneame", "meetup.com": "meetup", "medium.com": "medium",
              "djangoproject.com": "django", "python.org": "python", "spotify.com": "spotify"}
LINK_RE = re.compile(r'<a [^>]*href="https?://(?:www\.)?([^/"]+)[^"]*"[^>]*>(?!<(?:img|svg|iframe))')
_LINK_ICON = {}


def link_icons(html, settings):
    """Put the site's icon inside every link to LinkedIn, GitHub, X, YouTube, Wikipedia and the rest, before its text."""
    def icon(name):
        if name in ("pybcn", "meneame"):   # the two logos that are an image, not a mark drawn in the theme
            return f'<span class="link-icon icon-{name}"></span> '
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
        og_card(content)
        content.schema_type = PAGE_TYPES.get(getattr(content, "slug", ""), "WebPage")
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
    shown = not unpublished(content)   # a draft kept out of the output gets no small copies: they would be files of its own
    _PEEK_PHOTOS.add(m.group(1)[len("/images/posts/"):]) if shown and m and m.group(1).startswith("/images/posts/") else None
    cover = getattr(content, "cover", "")
    if cover.startswith("/images/posts/"):   # an Archive cover that is a restored photo: the same small copy
        content.cover_card_url = f"{site}/images/posts/card/{cover[len('/images/posts/'):].rsplit('.', 1)[0]}.webp"
        if shown:
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
    if shown:
        og_card(content)   # a draft kept out of the output has no page to share, so no card is drawn for it


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
_DRAFTS = []           # the posts with Status: draft; in production nothing of them reaches the output (hide_drafts)
_PAGES = []            # every page written, hidden ones too: a page may use a post's image, and then that image stays
_PEEK_PHOTOS = set()   # the restored photos a list shows small: relative to images/posts/


def unpublished(content):
    """True for a draft in a build that writes no drafts (publishconf.py): nothing of it may reach the output."""
    return getattr(content, "status", "") == "draft" and not content.settings.get("DRAFT_SAVE_AS")


def image_files(content):
    """The files under images/ a post or a page uses, relative to the output: its Cover and the images in its text."""
    files = set(re.findall(r'"(?:\{static\})?/(images/[^"]+)"', content._content or ""))
    cover = getattr(content, "cover", "")
    if cover:
        files.add(cover.lstrip("/") if cover.startswith("/") else f"images/covers/{cover}")
    return files


def draft_only_files():
    """The image files only the drafts use, relative to the output: each draft's Cover, the images in its text, and every
    file under images/posts/<slug>/. A file a published post or a page also uses is not one of them."""
    used = set().union(*(image_files(c) for c in _ARTICLES + _PAGES))
    files = set()
    for d in filter(unpublished, _DRAFTS):   # locally every draft is written, with its images: nothing to keep out
        files |= image_files(d)
        base = d.settings["PATH"]
        for root, _, names in os.walk(os.path.join(base, "images", "posts", d.slug)):
            files.update(os.path.relpath(os.path.join(root, n), base) for n in names)
    return files - used


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
    for d in generator.drafts:   # Pelican reads draft.category without getattr, and this site has no categories
        if not hasattr(d, "category"):
            d.category = Category(generator.settings["DEFAULT_CATEGORY"], generator.settings)
    lint(generator)
    _ARTICLES[:] = list(generator.articles)
    _DRAFTS[:] = list(generator.drafts)
    generator.context["stats"] = s = stats(_ARTICLES, generator.settings)
    _STATS.clear(); _STATS.update(s)
    zero = [k for k, v in s.items() if isinstance(v, int) and v == 0]
    if zero:
        raise SystemExit(f"stats: these figures came out as zero, so something stopped counting: {', '.join(zero)}")
    # the neighbours, for the previous and next links at the end of a post (articles come newest first)
    for i, article in enumerate(_ARTICLES):
        article.next_article = _ARTICLES[i - 1] if i > 0 else None
        article.prev_article = _ARTICLES[i + 1] if i + 1 < len(_ARTICLES) else None


def remember_pages(generator):
    _PAGES[:] = list(generator.pages) + list(generator.hidden_pages)


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
    for name in ("feed.xsl", "sitemap.xsl"):   # the sitemap template writes its own stylesheet instruction
        xsl = os.path.join(pelican.output_path, "theme", name)
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
    kept_out = draft_only_files()   # a cover only a draft uses gets no card copy in production: the cover itself leaves too
    for name in sorted(os.listdir(src_dir)):
        src = os.path.join(src_dir, name)
        if not os.path.isfile(src) or f"images/covers/{name}" in kept_out:
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


# --- share cards --------------------------------------------------------------

OG_SIZE = (1200, 630)   # what LinkedIn, X, WhatsApp and Slack ask for: a 1.91:1 image, 1200 px wide
OG_DESIGN = "1"         # the layout's version: it is part of every card's hash, so a new design gives every card a new address
OG_FRAME = "2"          # the same, for the copy of a small cover (2: the cover fills the frame, the blur only fills the bands)
OG_COLORS = {"bg": (0x16, 0x16, 0x15), "fg": (0xe9, 0xe6, 0xdf), "muted": (0xa3, 0xa3, 0x9c), "blue": (0x8a, 0xb4, 0xe6)}   # og.png's ground and the dark palette
_OG_QUEUE = {}          # file name under images/og/ -> ("card", title, line, note, cover file) or ("frame", cover file): what write_og_cards draws at the end of the build


def og_card(content):
    """Decide the share card of a post or a page: its address, type and alt text. The file is drawn by write_og_cards.
    The address carries a hash of everything the card shows, so a changed title or cover gives a new address and the
    platforms fetch the new card. The home keeps og.png, the designed card of the whole site."""
    from pelican.contents import Article, Page
    if not isinstance(content, (Article, Page)) or getattr(content, "save_as", "") == "index.html":
        return   # a static file (an image, a file under extra/) is a content object too, and needs no card
    title = html.unescape(re.sub(r"<[^>]+>", "", getattr(content, "title", "") or "")).strip()
    date = getattr(content, "date", None)
    line = ""
    if date is not None:
        when = content.settings["JINJA_FILTERS"]["fecha_es"](date)
        label = getattr(content, "kind_label", "")
        line = f"{label}, {when}" if label and getattr(content, "section", "") != "archive" else when   # an Archive card shows its date only
    cover = getattr(content, "cover", "")
    base = content.settings["PATH"]
    cover_file = ""
    if cover:
        candidates = (base + cover, os.path.join(base, "extra") + cover) if cover.startswith("/") else (os.path.join(base, "images", "covers", cover),)
        cover_file = next((c for c in candidates if os.path.isfile(c)), "")
    content.og_image_width, content.og_image_height = OG_SIZE
    content.og_uses_cover = False
    # a Portfolio post shares its cover, made for the post, not a card. A cover at least PORTFOLIO_SHARE_MIN_WIDTH
    # wide goes as it is; a narrower one (the old covers, 800 px or less) goes as a 1200x630 copy: the cover in the
    # middle, over a blurred and darker copy of itself, so a platform shows it large without a blurred enlargement
    if date is not None and getattr(content, "section", "") == "portfolio" and cover_file:
        size = image_size(cover_file)
        content.og_image_alt = f"Portada de «{title}»" + (f", {line}" if line else "") + ". Hic sunt trolls, el blog de David Arcos."
        content.og_uses_cover = True   # the post's own image (its microdata) is the cover, whichever file is shared
        if size[0] and size[0] >= content.settings.get("PORTFOLIO_SHARE_MIN_WIDTH", 1200):
            site = content.settings["SITEURL"]
            content.og_image = f"{site}{cover}" if cover.startswith("/") else f"{site}/images/covers/{cover}"
            content.og_image_type = "image/png" if cover_file.lower().endswith(".png") else "image/jpeg"
            content.og_image_width, content.og_image_height = size
            return   # no card to draw
        digest = hashlib.sha256()
        for part in (OG_FRAME, str(content.settings.get("CARD_VERSION", 1))):
            digest.update(part.encode("utf-8") + b"\0")
        with open(cover_file, "rb") as f:
            digest.update(f.read())
        name = f"{content.slug}-{digest.hexdigest()[:10]}.jpg"
        _OG_QUEUE[name] = ("frame", cover_file)
        content.og_image = f"{content.settings['SITEURL']}/images/og/{name}"
        content.og_image_type = "image/jpeg"
        return
    # a page has no kind and no date: its summary goes under the title instead
    note = "" if date is not None else html.unescape(re.sub(r"<[^>]+>", "", getattr(content, "summary", "") or "")).strip()
    digest = hashlib.sha256()
    for part in (OG_DESIGN, str(content.settings.get("CARD_VERSION", 1)), title, line, note):
        digest.update(part.encode("utf-8") + b"\0")
    if cover_file:
        with open(cover_file, "rb") as f:
            digest.update(f.read())
    ext = "jpg" if cover_file else "png"   # a photo compresses as JPEG, flat colour and text as PNG
    name = f"{content.slug}-{digest.hexdigest()[:10]}.{ext}"
    _OG_QUEUE[name] = ("card", title, line, note, cover_file)
    content.og_image = f"{content.settings['SITEURL']}/images/og/{name}"
    content.og_image_type = "image/jpeg" if cover_file else "image/png"
    content.og_image_alt = f"«{title}»" + (f", {line}" if line else "") + ". Hic sunt trolls, el blog de David Arcos."


PAGE_TYPES = {"sobre-el-blog": "AboutPage", "cv": "ProfilePage"}   # the schema.org type of a page, for its microdata; any other page is a WebPage


_OG_FONTS = {}
_OG_FACES = {}


def _og_font(path, size, weight):
    """A size and a weight of one of the theme's variable fonts (Inter has an optical size axis, Fira Code has not).
    Kept once made: loading a woff2 file decompresses it, and a card asks for a font a dozen times."""
    from PIL import ImageFont
    if (path, size, weight) in _OG_FONTS:
        return _OG_FONTS[(path, size, weight)]
    font = ImageFont.truetype(path, size)
    axes = [a["name"] for a in font.get_variation_axes()]
    font.set_variation_by_axes([min(size, 32) if a == b"Optical size" else weight for a in axes])
    _OG_FONTS[(path, size, weight)] = font
    return font


def _og_wrap(text, font, width):
    """The words of the text in lines no wider than width."""
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and font.getlength(trial) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    return lines + ([current] if current else [])


def draw_og_card(title, line, note, cover_file, fonts, avatar):
    """One share card: the author and the blog at the top, the title, the kind and the date (or a page's summary), the
    domain at the bottom, and the post's cover as a panel on the right when there is one. The title takes the largest
    size that fits, and the block sits in the middle of the free space, so a short title does not leave a hole."""
    from PIL import Image, ImageDraw, ImageOps
    W, H = OG_SIZE
    margin = 64
    card = Image.new("RGB", (W, H), OG_COLORS["bg"])
    right = W - margin
    if cover_file:
        panel_x = 700
        with Image.open(cover_file) as im:
            im.draft("RGB", (W - panel_x, H))   # a large JPEG decodes at a fraction of its size, still larger than the panel
            panel = ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"), (W - panel_x, H), Image.LANCZOS)
        card.paste(panel, (panel_x, 0))
        # the seam: the ground fades into the photo over 90 px, so the panel reads as part of the card
        fade = Image.linear_gradient("L").rotate(-90, expand=True).resize((90, H))   # opaque at the edge of the text, clear 90 px into the photo
        card.paste(Image.new("RGB", (90, H), OG_COLORS["bg"]), (panel_x, 0), fade)
        right = panel_x - 40
    draw = ImageDraw.Draw(card)
    # the header: the photo in a circle, the name, the blog
    size = 72
    if avatar not in _OG_FACES:   # the round photo is the same on every card: made once
        with Image.open(avatar) as im:
            face = ImageOps.fit(im.convert("RGB"), (size, size), Image.LANCZOS)
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
        _OG_FACES[avatar] = (face, mask.resize((size, size), Image.LANCZOS))
    face, mask = _OG_FACES[avatar]
    card.paste(face, (margin, margin), mask)
    draw.text((margin + size + 20, margin + 6), "David Arcos", font=_og_font(fonts["inter"], 30, 650), fill=OG_COLORS["fg"])
    draw.text((margin + size + 20, margin + 44), "Hic sunt trolls", font=_og_font(fonts["inter"], 24, 400), fill=OG_COLORS["muted"])
    footer = H - margin - 30
    draw.text((margin, footer), "davidarcos.net", font=_og_font(fonts["inter"], 26, 500), fill=OG_COLORS["muted"])
    # what goes between: the title, then the kind and the date, or a page's summary in two lines at most
    top, bottom = margin + size + 40, footer - 34
    width = right - margin
    below = []   # (text, font, colour, line height)
    if line:
        px = 28
        while px > 20 and _og_font(fonts["fira"], px, 450).getlength(line) > width:
            px -= 2   # "Mesa redonda, 19 de noviembre de 2024" must not run into the photo
        below.append((line, _og_font(fonts["fira"], px, 450), OG_COLORS["blue"], px + 6))
    if note:
        font = _og_font(fonts["inter"], 28, 400)
        wrapped = _og_wrap(note, font, width)
        if len(wrapped) > 2:
            wrapped = wrapped[:2]
            while font.getlength(wrapped[1] + "…") > width:
                wrapped[1] = wrapped[1].rsplit(" ", 1)[0]
            wrapped[1] += "…"
        below += [(text, font, OG_COLORS["muted"], 36) for text in wrapped]
    below_h = (22 + sum(h for *_, h in below)) if below else 0
    for px in (88, 76, 64, 58, 52, 46, 40):
        font = _og_font(fonts["inter"], px, 700)
        lines = _og_wrap(title, font, width)
        step = round(px * 1.16)
        most = 3 if px > 46 else 4   # a long title may take a fourth line at the small sizes rather than lose its end
        if len(lines) <= most and len(lines) * step + below_h <= bottom - top:
            break
    if len(lines) > most:
        lines = lines[:most]
        while font.getlength(lines[-1] + "…") > width:
            lines[-1] = lines[-1].rsplit(" ", 1)[0] if " " in lines[-1] else lines[-1][:-1]
        lines[-1] += "…"
    y = top + (bottom - top - (len(lines) * step + below_h)) // 2
    for text in lines:
        draw.text((margin, y), text, font=font, fill=OG_COLORS["fg"])
        y += step
    y += 22
    for text, f, colour, h in below:
        draw.text((margin, y), text, font=f, fill=colour)
        y += h
    return card


def _og_trim(im):
    """The image without the flat bars an old cover may carry (a 4:3 video letterboxed in black, say): the box of the
    pixels that differ from the corner colour, when that box is clearly smaller than the image."""
    from PIL import Image, ImageChops
    corner = im.getpixel((0, 0))
    diff = ImageChops.difference(im, Image.new("RGB", im.size, corner)).convert("L")
    box = diff.point(lambda v: 255 if v > 24 else 0).getbbox()
    if box and (box[2] - box[0]) * (box[3] - box[1]) < 0.96 * im.width * im.height:
        return im.crop(box)
    return im


def draw_og_frame(cover_file):
    """The 1200x630 copy of a cover narrower than 1200 px: the cover enlarged until it touches two opposite edges, as
    large as the frame allows, and a blurred, darker copy of itself only in the bands its proportion leaves free. A
    platform shows the copy at about half its width, so every pixel given to the cover counts; the old covers are
    small, and an enlargement of them is soft but whole."""
    from PIL import Image, ImageEnhance, ImageFilter
    W, H = OG_SIZE
    with Image.open(cover_file) as im:
        im = _og_trim(im.convert("RGB"))
    scale = max(W / im.width, H / im.height)
    back = im.resize((round(im.width * scale) + 2, round(im.height * scale) + 2), Image.LANCZOS)
    left, top = (back.width - W) // 2, (back.height - H) // 2
    back = back.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(36))
    back = ImageEnhance.Brightness(back).enhance(0.5)
    back = ImageEnhance.Color(back).enhance(0.8)
    fit = min(W / im.width, H / im.height)
    front = im.resize((round(im.width * fit), round(im.height * fit)), Image.LANCZOS)
    back.paste(front, ((W - front.width) // 2, (H - front.height) // 2))
    return back


def _og_job(job):
    """Draw and save one card or one framed cover: the unit of work of write_og_cards, run in a worker process."""
    path, spec, fonts, avatar = job
    if spec[0] == "frame":
        draw_og_frame(spec[1]).save(path, "JPEG", quality=90, subsampling=0)   # full colour detail: the blurred ground bands at 4:2:0
        return
    _kind, title, line, note, cover_file = spec
    card = draw_og_card(title, line, note, cover_file, fonts, avatar)
    if path.endswith(".jpg"):
        card.save(path, "JPEG", quality=85)   # optimize and progressive cost 4x the time for 10 % of the size
    else:
        card.save(path, "PNG", compress_level=6)   # level 9 or optimize cost 3x the time for 5 % of the size


def write_og_cards(pelican):
    """Draw every share card og_card decided, in parallel: each card is independent. A card whose file already exists
    has the same inputs (its name is their hash), so it is not drawn again."""
    if not _OG_QUEUE:
        return
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    theme = pelican.settings["THEME"]
    fonts = {"inter": os.path.join(theme, "static", "fonts", "inter-latin.woff2"),
             "fira": os.path.join(theme, "static", "fonts", "fira-code-latin.woff2")}
    avatar = os.path.join(theme, "static", "img", "david.arcos.jpg")
    out_dir = os.path.join(pelican.output_path, "images", "og")
    os.makedirs(out_dir, exist_ok=True)
    jobs = [(os.path.join(out_dir, name), spec, fonts, avatar) for name, spec in sorted(_OG_QUEUE.items())
            if not os.path.exists(os.path.join(out_dir, name))]
    if jobs:
        # fork, not the default forkserver of Python 3.14: a forked worker has this module already, a new one would
        # have to import the plugin by name from a path it does not know
        with ProcessPoolExecutor(max_workers=os.cpu_count(), mp_context=multiprocessing.get_context("fork")) as pool:
            list(pool.map(_og_job, jobs, chunksize=8))
    print(f"share cards: {len(_OG_QUEUE)} ({len(jobs)} drawn)")


def hide_drafts(pelican):
    """In production nothing of a draft reaches the output. Its cards are never drawn (decorate, write_card_covers); its
    image files are copied with the rest of content/images (STATIC_PATHS), so the ones only it uses are removed here.
    Then the output is checked, last of all: a file of a draft, a small copy of one, or a share card named after a draft
    stops the build, so a new kind of derived image cannot leak a draft without being noticed."""
    drafts = list(filter(unpublished, _DRAFTS))
    if not drafts:
        return
    out = pelican.output_path
    only = draft_only_files()
    for rel in sorted(only):
        path = os.path.join(out, rel)
        if os.path.isfile(path):
            os.remove(path)
        folder = os.path.dirname(path)
        while folder != out and os.path.isdir(folder) and not os.listdir(folder):
            os.rmdir(folder)   # the empty folder of a draft (images/posts/<slug>/) names the draft too
            folder = os.path.dirname(folder)
    stems = {os.path.splitext(rel)[0] for rel in only}   # images/covers/<name>: what a card copy of the file is named after
    og = re.compile(r"^images/og/(?:%s)-[0-9a-f]{10}\.(?:jpg|png)$" % "|".join(re.escape(d.slug) for d in drafts))
    leaks = []
    for root, _, names in os.walk(os.path.join(out, "images")):
        for name in names:
            rel = os.path.relpath(os.path.join(root, name), out)
            if rel in only or os.path.splitext(rel)[0].replace("/card/", "/") in stems or og.match(rel):
                leaks.append(rel)
    if leaks:
        raise SystemExit("drafts: these files of a draft reached the output:\n  " + "\n  ".join(sorted(leaks)))
    print(f"drafts kept out of the output: {len(drafts)} ({len(only)} files removed)")


def page_modified(content):
    """A page with no date gets the date of the last commit that changed its source, for the sitemap's lastmod. The build
    needs the full history for this (fetch-depth: 0 in the deploy workflow); outside git, the page keeps no date."""
    if type(content).__name__ != "Page" or getattr(content, "modified", None) or getattr(content, "date", None):
        return
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cI", "--", content.source_path], capture_output=True, text=True,
                             cwd=os.path.dirname(content.source_path), timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return
    if out:
        content.modified = datetime.fromisoformat(out)


def register():
    signals.content_object_init.connect(page_modified)
    signals.content_object_init.connect(decorate)
    signals.article_generator_finalized.connect(remember_articles)
    signals.page_generator_finalized.connect(remember_pages)
    signals.finalized.connect(write_stubs)
    signals.finalized.connect(style_feed)
    signals.finalized.connect(version_theme_urls)
    signals.finalized.connect(write_card_covers)
    signals.finalized.connect(write_og_cards)
    signals.finalized.connect(hide_drafts)   # last: it checks what every handler above wrote
