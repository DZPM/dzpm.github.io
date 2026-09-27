#!/usr/bin/env python3
"""Serve output/ locally the way GitHub Pages does: text files as UTF-8, on http://127.0.0.1:8000.
One difference: every response says no-cache, so after a rebuild the browser asks again and never shows an old stylesheet.
With --html-only it serves the pages and answers 404 for every other file (CSS, scripts, images, fonts, the search
index): the site as a reader sees it when its static files fail to load. --allow-images lets images through as well.
--no-images is the other way round: everything loads but the images. --no-js blocks the scripts only.
Usage: serve.py [port] [--html-only [--allow-images] | --no-images | --no-js]"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".txt": "text/plain; charset=utf-8", ".xml": "application/xml; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8", "": "text/plain; charset=utf-8"}

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")   # revalidate every time: a local build changes files without changing their address
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


IMAGES = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico")


class HtmlOnly(Handler):
    allowed = (".html",)

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path) or path.lower().endswith(self.allowed):
            return super().send_head()
        self.send_error(404, "Static files are off for this test")
        return None


class Blocking(Handler):
    blocked = ()

    def send_head(self):
        if self.translate_path(self.path).lower().endswith(self.blocked):
            self.send_error(404, "Off for this test")
            return None
        return super().send_head()


class NoImages(Blocking):
    blocked = IMAGES


class NoJs(Blocking):
    blocked = (".js", ".mjs", ".wasm")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    port = int(args[0]) if args else 8000
    handler = NoImages if "--no-images" in sys.argv else NoJs if "--no-js" in sys.argv else Handler
    if "--html-only" in sys.argv:
        handler = type("Test", (HtmlOnly,), {"allowed": (".html",) + (IMAGES if "--allow-images" in sys.argv else ())})
    ThreadingHTTPServer(("127.0.0.1", port), lambda *a, **k: handler(*a, directory=ROOT, **k)).serve_forever()
