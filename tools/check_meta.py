#!/usr/bin/env python3
"""Assert every page of the built site is complete for a shared link and a search result.

A link to the site shows a card: an image, a title and a description, read from the page's meta tags. When a tag is
missing, or the image is not where the tag points, the card is poor or empty and nothing tells the owner. This check
reads every page that has a canonical address and is not a redirect stub (a stub names its target as canonical and
moves on with a meta refresh: it is not meant to be shared), and fails
when one lacks og:title, og:description, og:image, og:image:alt or twitter:card, when og:image is not a file of the
build, or when og:image:width and og:image:height do not match that file.

A card (images/og/, and og.png) must be 1200x630: the generated cards, and the framed copy of a small cover. A post of
the talks and articles shares its cover instead when the cover is at least 1200 px wide (docs/adr/0011); a narrower
shared cover fails, since the build shares a 1200x630 copy of it. Any other page that shares an image that is not a
card fails.

The description is the post's or page's Summary. A shared link shows it and LinkedIn warns under 100 characters; a
search result shows about 155. For the talks and articles (Charlas y artículos) and for the pages, a description under
100 or over 160 characters fails. For the Archive, written for another time, and for the Notas, which take no Summary
and are described by their first lines, it only warns.

Usage:  python tools/check_meta.py output
"""

import os
import pathlib
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

REQUIRED = ("og:title", "og:description", "og:image", "og:image:alt", "twitter:card")
SIZE = (1200, 630)
SHORT, LONG = 100, 160
LENIENT = {"Archivo", "Notas"}   # the article:section values that only warn on the description's length
PORTFOLIO = "Charlas y artículos"   # the article:section of a post that may share its cover
COVER_MIN = 1200   # a Portfolio cover narrower than this is shared through its 1200x630 copy, never as it is


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.canonical = None
        self.refresh = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            self.refresh = True
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key and key not in self.meta:
                self.meta[key] = a.get("content") or ""
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")


def image_file(out, url):
    """The file of the build that an og:image address names, or None when it names no file of the build."""
    path = urlparse(url).path.lstrip("/")
    full = os.path.join(out, path)
    return full if path and os.path.isfile(full) else None


def main(out):
    if not any(pathlib.Path(out).rglob("*.html")):   # an empty or missing build must fail, not pass with nothing checked
        print(f"meta: no HTML pages in {out}: nothing to check (is the build empty?)")
        return 1
    from PIL import Image
    pages = 0
    errors, warnings = [], []
    sizes = {}
    for base, _dirs, files in os.walk(out):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(base, f)
            page = Page()
            page.feed(open(path, encoding="utf-8").read())
            if not page.canonical or page.refresh:
                continue
            pages += 1
            rel = os.path.relpath(path, out)
            for key in REQUIRED:
                if not page.meta.get(key, "").strip():
                    errors.append(f"{rel}: no {key}")
            url = page.meta.get("og:image", "")
            if url:
                img = image_file(out, url)
                if img is None:
                    errors.append(f"{rel}: og:image {url} is not a file of the build")
                else:
                    if img not in sizes:
                        with Image.open(img) as im:
                            sizes[img] = im.size
                    w, h = sizes[img]
                    declared = (page.meta.get("og:image:width", ""), page.meta.get("og:image:height", ""))
                    if declared != (str(w), str(h)):
                        errors.append(f"{rel}: og:image is {w}x{h}, but the page says {declared[0]}x{declared[1]}")
                    card = urlparse(url).path.startswith("/images/og/") or urlparse(url).path == "/og.png"
                    if card and (w, h) != SIZE:
                        errors.append(f"{rel}: og:image is {w}x{h}, not {SIZE[0]}x{SIZE[1]}")
                    elif not card and page.meta.get("article:section") != PORTFOLIO:
                        errors.append(f"{rel}: shares {urlparse(url).path}, not a card, and it is not a talk or an article")
                    elif not card and w < COVER_MIN:
                        errors.append(f"{rel}: shares a cover {w} px wide, under {COVER_MIN}: it should share its 1200x630 copy")
            text = page.meta.get("og:description", "")
            if text and not SHORT <= len(text) <= LONG:
                msg = f"{rel}: description of {len(text)} characters, want {SHORT} to {LONG}"
                (warnings if page.meta.get("article:section") in LENIENT else errors).append(msg)
    for w in warnings:
        print(f"  warning: {w}")
    if errors:
        print(f"meta: {len(errors)} problem(s) on {pages} pages:")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"meta: {pages} pages complete ({len(warnings)} archive or note description(s) outside {SHORT} to {LONG}, warned)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "output"))
