#!/usr/bin/env python3
"""Assert every page of the built site is complete for a shared link and a search result.

A link to the site shows a card: an image, a title and a description, read from the page's meta tags. When a tag is
missing, or the image is not where the tag points, the card is poor or empty and nothing tells the owner. This check
reads every page that has a canonical address and is not a redirect stub (a stub names its target as canonical and
moves on with a meta refresh: it is not meant to be shared), and fails
when one lacks og:title, og:description, og:image, og:image:alt or twitter:card, when og:image is not a file of the
build, or when that file is not 1200x630.

The description is the post's or page's Summary. A shared link shows it and LinkedIn warns under 100 characters; a
search result shows about 155. For the talks and articles (Charlas y artículos) and for the pages, a description under
100 or over 160 characters fails. For the Archive, written for another time, and for the Notas, which take no Summary
and are described by their first lines, it only warns.

Usage:  python tools/check_meta.py output
"""

import os
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

REQUIRED = ("og:title", "og:description", "og:image", "og:image:alt", "twitter:card")
SIZE = (1200, 630)
SHORT, LONG = 100, 160
LENIENT = {"Archivo", "Notas"}   # the article:section values that only warn on the description's length


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
                    if sizes[img] != SIZE:
                        errors.append(f"{rel}: og:image is {sizes[img][0]}x{sizes[img][1]}, not {SIZE[0]}x{SIZE[1]}")
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
