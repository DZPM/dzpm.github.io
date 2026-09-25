#!/usr/bin/env python3
"""Serve output/ locally the way GitHub Pages does: text files as UTF-8, on http://127.0.0.1:8000."""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".txt": "text/plain; charset=utf-8", ".xml": "application/xml; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8", "": "text/plain; charset=utf-8"}

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    ThreadingHTTPServer(("127.0.0.1", port), lambda *a, **k: Handler(*a, directory=ROOT, **k)).serve_forever()
