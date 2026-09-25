#!/usr/bin/env python3
"""Tell the search engines that use IndexNow (Bing, Yandex, Naver, Seznam; not Google) which pages exist.

Reads the site's sitemap and posts every URL in it to api.indexnow.org in one request, with the key
that is served at the site's root. Run once after the site goes live, and again after a batch of
changes; a single new post is picked up by the crawl anyway.

Usage:  python tools/indexnow.py            (after `make build` with publishconf, so the sitemap carries the domain)
        python tools/indexnow.py --dry-run  (prints the request, sends nothing)
"""
import json
import os
import re
import sys
import urllib.request

SITE = "https://davidarcos.net"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def key():
    for name in os.listdir(os.path.join(HERE, "content", "extra")):
        if re.fullmatch(r"[0-9a-f]{32}\.txt", name):
            return name[:-4]
    raise SystemExit("no IndexNow key file in content/extra/ (a 32 hex character name, holding the same characters)")


def urls():
    # the sitemap of the last build, so the list is the site's own, whatever the live server answers
    with open(os.path.join(HERE, "output", "sitemap.xml"), encoding="utf-8") as f:
        found = re.findall(r"<loc>([^<]+)</loc>", f.read())
    return [u if u.startswith("http") else SITE + u for u in found]


def main():
    k = key()
    body = {"host": SITE.removeprefix("https://"), "key": k, "keyLocation": f"{SITE}/{k}.txt", "urlList": urls()}
    print(f"{len(body['urlList'])} URLs, key {k[:6]}...")
    if "--dry-run" in sys.argv:
        print(json.dumps(body, indent=1)[:600])
        return
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(r.status, r.reason)   # 200 or 202 means accepted


if __name__ == "__main__":
    main()
