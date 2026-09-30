#!/usr/bin/env python3
"""Tell the search engines that use IndexNow (Bing, Yandex, Naver, Seznam; not Google) which pages exist.

Reads the site's sitemap and posts every URL in it to api.indexnow.org in one request, with the key
that is served at the site's root. Run once after the site goes live, and again after a batch of
changes; a single new post is picked up by the crawl anyway.

With --home it sends the home page only. The deploy does that after a push that adds or changes a post: the home
lists every new post, so one URL is enough for the engines to find it, and a push that changes only the theme or
the tools sends nothing.

Usage:  python tools/indexnow.py            (after `make build` with publishconf, so the sitemap carries the domain)
        python tools/indexnow.py --home     (the home page only; needs no build)
        python tools/indexnow.py --dry-run  (prints the request, sends nothing)
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

SITE = "https://davidarcos.net"
# what api.indexnow.org answers (https://www.indexnow.org/documentation)
MEANING = {
    200: "OK, the URLs were received",
    202: "accepted, the key is not validated yet",
    400: "bad request",
    403: "forbidden, the key is not valid (the key file is missing or does not match)",
    422: "unprocessable, a URL is not on this host, or the key does not match the scheme",
    429: "too many requests",
}
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
    body = {"host": SITE.removeprefix("https://"), "key": k, "keyLocation": f"{SITE}/{k}.txt", "urlList": [f"{SITE}/"] if "--home" in sys.argv else urls()}
    print(f"{len(body['urlList'])} URLs, key {k[:6]}...")
    if "--dry-run" in sys.argv:
        print(json.dumps(body, indent=1)[:600])
        return
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"indexnow: no answer ({e})")
        return 1
    print(f"indexnow: {status} {MEANING.get(status, 'unexpected answer')}")
    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main())
