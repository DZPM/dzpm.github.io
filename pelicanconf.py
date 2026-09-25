"""Pelican settings for davidarcos.net. Local build; publishconf.py overrides for production."""

import datetime
import hashlib
import os
import re
import logging
import subprocess
import sys

sys.path.insert(0, "plugins")
from hst import EmbedExtension, num_es, mark_years  # noqa: E402

AUTHOR = "David Arcos"
SITENAME = "David Arcos"
SITESUBTITLE = "Hic sunt trolls"
SITEURL = ""
SITEDESCRIPTION = "Charlas, vídeos y artículos de David Arcos, y el archivo del blog."

PATH = "content"
ARTICLE_PATHS = ["posts"]
PAGE_PATHS = ["pages"]
STATIC_PATHS = ["images", "extra"]
# the IndexNow key file (tools/indexnow.py): a 32 hex character name at the root, public by design
_INDEXNOW = [f for f in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "extra")) if re.fullmatch(r"[0-9a-f]{32}\.txt", f)]
EXTRA_PATH_METADATA = {
    "extra/favicon.ico": {"path": "favicon.ico"},
    "extra/icon-32.png": {"path": "icon-32.png"},
    "extra/icon-192.png": {"path": "icon-192.png"},
    "extra/apple-touch-icon.png": {"path": "apple-touch-icon.png"},
    "extra/robots.txt": {"path": "robots.txt"},
    "extra/CNAME": {"path": "CNAME"},   # the custom domain, read by GitHub Pages and by publishconf; it enters at the cutover
    "extra/og.png": {"path": "og.png"},
    "extra/.well-known/index.html": {"path": ".well-known/index.html"},   # empty, so the directory serves a blank page instead of a listing
    "extra/.well-known/keybase.txt": {"path": ".well-known/keybase.txt"},
    "extra/.well-known/security.txt": {"path": ".well-known/security.txt"},
    "extra/files/1180550273-monkey-sgae.gif": {"path": "files/1180550273-monkey-sgae.gif"},
    **{f"extra/{f}": {"path": f} for f in _INDEXNOW},
}
REDIRECTS_TO_BLOG = ["blog/2006/11/14/ya-vuelve-a-funcionar-gravatarcom", "2006/11/14/ya-vuelve-a-funcionar-gravatarcom", "blog/author/dzpm", "blog/tag/yopino"]   # a post not migrated that still gets readers; the author page; a tag WordPress had under another name
REDIRECTS_TO_BLOG += [f"blog/tag/{t}" for t in ['animaciones', 'arduino', 'best-practices', 'bilbao', 'drupal', 'ciencia', 'encuesta', 'entrevista', 'eventos', 'fabric', 'fiberparty', 'flickr', 'legal', 'libros', 'soundstorm', 'ssh', 'festafib', 'gamerachan', 'gatitos', 'inocentada', 'linux', 'logs', 'musica', 'nosql', 'oferta-de-trabajo', 'podcast', 'precariedad', 'redis', 'south', 'sqlalchemy', 'tv', 'twisted', 'zaragoza']]   # tags retired in the 2026 review
REDIRECTS = {"mapa": ("Sobre el blog", "sobre-el-blog/#mapa"), "feed": ("Feed", "blog/feed.xml"), "blog/feed": ("Feed", "blog/feed.xml")}   # old page addresses: title and where the content lives now; the two feed addresses get a stub for browsers, the edge rule for readers
REDIRECTS.update({f"blog/tag/{old}": (new, f"blog/etiquetas/{new_slug}/") for old, new, new_slug in [('amsterdam', 'Viajes', 'viajes'), ('bruselas', 'Viajes', 'viajes'), ('complejidad', 'Problemas Complejos', 'problemas-complejos'), ('computacion-cuantica', 'Quantum Computing', 'quantum-computing'), ('cps', 'Problemas Complejos', 'problemas-complejos'), ('eduard', 'Personal', 'personal'), ('friends', 'Personal', 'personal'), ('meetup', 'Python Barcelona', 'python-barcelona'), ('pybcn', 'Python Barcelona', 'python-barcelona'), ('pydata', 'Python Barcelona', 'python-barcelona'), ('recuerdos', 'Personal', 'personal'), ('final-fantasy', 'Videojuegos', 'videojuegos'), ('leon', 'Viajes', 'viajes'), ('mallorca', 'Viajes', 'viajes'), ('mapas', 'Wardley Maps', 'wardley-maps'), ('menorca', 'Viajes', 'viajes'), ('reconocimiento-visual', 'Image Recognition', 'image-recognition'), ('star-wars', 'Cine', 'cine'), ('starcraft', 'Videojuegos', 'videojuegos'), ('viaje', 'Viajes', 'viajes'), ('visual-recognition', 'Image Recognition', 'image-recognition')]})   # tags merged in the 2026 review
IGNORE_FILES = [".#*"]  # the default ignores dot directories, which would drop .well-known

TIMEZONE = "Europe/Madrid"
DEFAULT_LANG = "es"
# no LOCALE: the site writes its own Spanish dates (fecha_es below), and asking for one makes the build depend
# on the locales a machine happens to have generated (the GitHub runner has none, and --fatal warnings would stop it)
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

THEME = "themes/hst"
PLUGIN_PATHS = ["plugins"]
PLUGINS = ["hst"]

# Addresses. Posts live at /blog/<slug>/ (docs/adr/0002). Everything Pelican
# would generate on top of that is switched off.
ARTICLE_URL = "blog/{slug}/"
ARTICLE_SAVE_AS = "blog/{slug}/index.html"
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"
INDEX_SAVE_AS = "blog/index.html"
DEFAULT_PAGINATION = False
ARCHIVES_SAVE_AS = ""
YEAR_ARCHIVE_SAVE_AS = ""
MONTH_ARCHIVE_SAVE_AS = ""
DAY_ARCHIVE_SAVE_AS = ""
AUTHOR_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
TAG_URL = "blog/etiquetas/{slug}/"
TAG_SAVE_AS = "blog/etiquetas/{slug}/index.html"
TAGS_URL = "blog/etiquetas/"
TAGS_SAVE_AS = "blog/etiquetas/index.html"
DRAFT_URL = "borradores/{slug}/"                # a post with Status: draft, to look at locally; publishconf.py turns it off
DRAFT_SAVE_AS = "borradores/{slug}/index.html"
DIRECT_TEMPLATES = ["index", "tags"]
TEMPLATE_PAGES = {
    "buscar.html": "blog/buscar/index.html",
    "404.html": "404.html",
    "sitemap.xml": "sitemap.xml",
    "llms-full.txt": "llms-full.txt",       # one line per post, for the models
    "llms.txt": "llms.txt",                 # the site for the models, with the figures the build counts
    "humans.txt": "humans.txt",             # the site for the humans, same figures
    "search.js": "theme/js/search.js",      # the one script, as a file: the CSP allows no inline script
}

# One feed, the last ten, full text. Everything else off.
FEED_DOMAIN = SITEURL
FEED_ATOM = "blog/feed.xml"
FEED_ATOM_URL = "blog/feed.xml"
FEED_MAX_ITEMS = 10
FEED_ALL_ATOM = None
FEED_RSS = None
FEED_ALL_RSS = None
CATEGORY_FEED_ATOM = None
CATEGORY_FEED_RSS = None
TAG_FEED_ATOM = None
TAG_FEED_RSS = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
TRANSLATION_FEED_ATOM = None
TRANSLATION_FEED_RSS = None

# A Summary is written by hand or does not exist. Never derived from the text.
SUMMARY_MAX_LENGTH = 0

MARKDOWN = {
    "extensions": [EmbedExtension(), "markdown.extensions.extra", "markdown.extensions.codehilite"],
    "extension_configs": {"markdown.extensions.codehilite": {"css_class": "highlight"}},
    "output_format": "html5",
}

SLUGIFY_SOURCE = "basename"
CACHE_CONTENT = False
LOAD_CONTENT_CACHE = False
DELETE_OUTPUT_DIRECTORY = True
OUTPUT_RETENTION = []

SOCIAL = (   # name, url, icon, the title of the footer icon
    ("LinkedIn", "https://www.linkedin.com/in/davidarcos", "linkedin", "in/davidarcos en LinkedIn"),
    ("GitHub", "https://github.com/DZPM", "github", "DZPM en GitHub"),
    ("Stack Overflow", "https://stackoverflow.com/users/30300/david-arcos", "stackoverflow", "David Arcos en Stack Overflow"),
    ("X", "https://x.com/DZPM", "x", "@DZPM en X"),
    ("Instagram", "https://www.instagram.com/dzpm/", "instagram", "@dzpm en Instagram"),
    ("Flickr", "https://www.flickr.com/photos/dzpm", "flickr", "dzpm en Flickr"),
    ("YouTube", "https://youtube.com/user/HicSuntTrolls", "youtube", "HicSuntTrolls en YouTube"),
    ("SlideShare", "https://www.slideshare.net/DZPM", "slideshare", "DZPM en SlideShare"),
    ("Keybase", "https://keybase.io/davidarcos", "keybase", "davidarcos en Keybase"),
    ("Python Barcelona", "https://pybcn.org/", "pybcn", "Python Barcelona"),   # not one of the author's profiles: no rel="me", no sameAs
)

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_es(d):
    """15 de junio de 2022"""
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_corta(d):
    """15 jun"""
    return f"{d.day} {MESES_CORTOS[d.month - 1]}"


def mes_corto(n):
    """6 -> Jun"""
    return MESES_CORTOS[int(n) - 1].capitalize()


def fecha_es_str(iso):
    """Same as fecha_es, from a YYYY-MM-DD string in front matter."""
    from datetime import date
    return fecha_es(date.fromisoformat(str(iso)[:10]))


ASSET_VERSION = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "dev"   # cache buster for style.css
# the fonts and the theme images are cached for a year at the edge: their address carries a hash of their content,
# so it changes when the file changes and only then (the commit would change it on every deploy, and a reader would download them again)
_THEME_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes", "hst", "static")
ASSET_HASH = {f"{d}/{f}": hashlib.sha256(open(os.path.join(_THEME_STATIC, d, f), "rb").read()).hexdigest()[:8]
              for d in ("fonts", "img") for f in sorted(os.listdir(os.path.join(_THEME_STATIC, d)))}
BUILD_DATE = datetime.datetime.now(datetime.timezone.utc).astimezone().replace(microsecond=0).isoformat()   # in a comment in the head of every page: the site says when it was generated, to whoever looks
JINJA_FILTERS = {"fecha_es": fecha_es, "fecha_corta": fecha_corta, "fecha_es_str": fecha_es_str, "mes_corto": mes_corto, "num_es": num_es, "yr": lambda s: mark_years(re.sub(r"<[^>]+>", "", s or ""))}   # a summary or an excerpt: no tags, and the years in their voice

# the publish build fails on any warning (make publish, CI) except these two, which the site understands:
# the empty alt on a restored photo is filled by the plugin. The local build keeps --fatal errors, because
# it has no SITEURL on purpose and Pelican warns about that before this filter is in place.
LOG_FILTER = [
    (logging.WARNING, "Empty alt attribute for image %s in %s"),
    (logging.WARNING, "Other images have empty alt attributes"),
]
