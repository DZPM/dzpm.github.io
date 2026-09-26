#!/usr/bin/env python3
"""Assert every iframe in the built site comes from an origin that its own page's CSP allows.

A browser blocks a frame that frame-src does not list, and it does so in silence: the reader sees an empty box, the
build sees nothing. This check makes the build see it. It reads each page's <meta http-equiv="Content-Security-Policy">,
takes frame-src (or child-src, then default-src, as the browser does when frame-src is absent), and checks the origin
of every <iframe src> against it.

Usage:  python tools/check_csp.py output
"""

import os
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.csp = None
        self.frames = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "content-security-policy":
            self.csp = a.get("content") or ""
        elif tag == "iframe":
            self.frames.append(a.get("src") or "")


def frame_sources(csp):
    """The source list that governs frames, or None when the policy says nothing about them."""
    directives = {}
    for part in csp.split(";"):
        words = part.split()
        if words:
            directives.setdefault(words[0].lower(), words[1:])
    for name in ("frame-src", "child-src", "default-src"):
        if name in directives:
            return directives[name]
    return None


def allowed(src, sources):
    u = urlparse(src)
    if not u.scheme and not u.netloc:
        return "'self'" in sources   # a relative address is the site itself
    origin = f"{u.scheme}://{u.netloc}".lower()
    for s in sources:
        s = s.lower()
        if s == "'none'":
            return False
        if s == origin or s == f"{u.scheme}:":
            return True
        if s.startswith(f"{u.scheme}://*.") and u.netloc.lower().endswith(s[len(f"{u.scheme}://*"):]):
            return True
    return False


def main(out):
    pages = frames = 0
    bad = []
    for base, _dirs, files in os.walk(out):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(base, f)
            page = Page()
            page.feed(open(path, encoding="utf-8").read())
            if not page.frames:
                continue
            pages += 1
            frames += len(page.frames)
            sources = frame_sources(page.csp) if page.csp is not None else None
            for src in page.frames:
                if sources is None:
                    bad.append((os.path.relpath(path, out), src, "no CSP on the page"))
                elif not allowed(src, sources):
                    bad.append((os.path.relpath(path, out), src, "frame-src does not allow it"))
    if bad:
        print(f"{len(bad)} iframe(s) the page CSP blocks:")
        for p, src, why in bad:
            print(f"  {p}: {src[:90]} ({why})")
        return 1
    print(f"csp: {frames} iframes on {pages} pages, all allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "output"))
