#!/usr/bin/env python3
"""Assert every link and source inside the built site that points at the site itself resolves to a file.

Posts link by hand to /blog/<slug>/, photos and covers by path; a typo lands on the 404 page and nothing
would say so. Redirect stubs are skipped (tools/check_stubs.py covers them); external links are not checked.

Usage:  python tools/check_links.py output
"""

import os
import re
import sys
from html.parser import HTMLParser

ATTRS = {("a", "href"), ("img", "src"), ("link", "href"), ("script", "src"), ("source", "srcset"), ("img", "srcset")}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if (tag, name) in ATTRS and value:
                for v in (value.split(",") if name == "srcset" else [value]):
                    self.found.append(v.strip().split(" ")[0])


def local(url):
    """The path inside the site for a link to it, or None for anything else."""
    url = url.split("#", 1)[0].split("?", 1)[0]
    if url.startswith("https://davidarcos.net/"):
        url = url[len("https://davidarcos.net"):]
    if not url.startswith("/") or url.startswith("//"):
        return None
    return url


def main(out):
    checked = 0
    bad = []
    for base, _dirs, files in os.walk(out):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(base, f)
            text = open(path, encoding="utf-8").read()
            if 'http-equiv="refresh"' in text[:2000]:
                continue
            p = Links()
            p.feed(text)
            for url in p.found:
                rel = local(url)
                if rel is None:
                    continue
                checked += 1
                target = os.path.join(out, rel.strip("/"))
                if not (os.path.isfile(target) or os.path.isfile(os.path.join(target, "index.html"))):
                    bad.append((os.path.relpath(path, out), url))
    if bad:
        for page, url in sorted(set(bad)):
            print(f"  {page}: {url}")
        raise SystemExit(f"internal links: {len(set(bad))} broken")
    print(f"internal links: {checked} checked, all resolve")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "output")
