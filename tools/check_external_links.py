#!/usr/bin/env python3
"""Check the external links of the pages that must stay alive: the Portfolio posts and the main pages.

The archive is not checked: its dead links are already shown as dead, on purpose. A link counts as dead only on
HTTP 404 or 410, a DNS failure or a TLS failure. A site that blocks robots (403, 429, LinkedIn's 999), a timeout
or a server error after the retries is "could not check", not dead.

Usage:  python tools/check_external_links.py output [--report report.md] [--section "Charlas y artículos"]

It also lists the pending media notes (plugins/hst.py, MEDIA_NOTE_LINE) on every page: a video or an audio that its
owner has not published yet, so the report reminds to look for it. They do not count as dead, and they do not change
the exit code.

It prints the counts and writes a Markdown report. Exit code 0 when no link is dead, 1 when one or more are,
2 when there is no page to check. Standard library only.
"""
import argparse
import concurrent.futures
import html
import html.parser
import pathlib
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SITE = "davidarcos.net"
PORTFOLIO = "Charlas y artículos"
PAGE_TYPES = ("WebSite", "WebPage", "AboutPage", "ProfilePage")   # the home and the main pages (their microdata type)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
TIMEOUT = 20
RETRIES = 2
WORKERS = 4
DEAD_STATUS = (404, 410)
PENDING = re.compile(r'<aside class="banner media-note media-pending"[^>]*>.*?<span><span>Aquí irá (.+?)\.</span><br><span>Lo añadiré cuando se publique en <a href="([^"]+)"[^>]*>(.+?)</a>')


class Page(html.parser.HTMLParser):
    """Reads the section, the page type and the external links of one built page."""

    def __init__(self):
        super().__init__()
        self.section, self.types, self.links = "", set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("property") == "article:section":
            self.section = a.get("content") or ""
        if a.get("itemtype", "").startswith("https://schema.org/"):
            self.types.add(a["itemtype"].rsplit("/", 1)[-1])
        if tag == "a" and a.get("href", "").startswith(("http://", "https://")):
            host = urllib.parse.urlsplit(a["href"]).hostname or ""
            if host != SITE and not host.endswith("." + SITE):
                self.links.append(a["href"])


def pending_media(out):
    """Return [(page, what, owner, url)] for every pending media note in the build."""
    found = []
    for path in sorted(pathlib.Path(out).rglob("index.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for what, url, owner in PENDING.findall(text):
            rel = path.parent.relative_to(out).as_posix()
            found.append(("/" if rel == "." else f"/{rel}/", *(html.unescape(re.sub(r"<[^>]+>", "", v)).strip() for v in (what, owner, url))))   # the owner may carry the site icon of its link
    return found


def pages_to_check(out, section):
    found = {}
    for path in sorted(pathlib.Path(out).rglob("index.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if 'http-equiv="refresh"' in text[:2000]:
            continue   # a redirect stub: its target is checked where it lives
        p = Page()
        p.feed(text)
        if p.section == section or p.types & set(PAGE_TYPES):
            rel = path.parent.relative_to(out).as_posix()
            found["/" if rel == "." else f"/{rel}/"] = p.links
    return found


def fetch(url, method):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as r:
            if method == "GET":
                r.read(1024)
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, ""
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, socket.gaierror):
            return None, "DNS failure"
        if isinstance(reason, ssl.SSLError) or "CERTIFICATE" in str(reason).upper():
            return None, "TLS failure"
        return None, f"network: {reason}"
    except (TimeoutError, socket.timeout):
        return None, "timeout"
    except (ssl.SSLError, ssl.CertificateError):
        return None, "TLS failure"
    except Exception as e:   # a bad URL or a protocol error: report it, do not stop the run
        return None, f"error: {type(e).__name__}"


def check(url):
    """Return (verdict, detail): verdict is ok, dead or unknown."""
    status, why = None, ""
    for attempt in range(RETRIES + 1):
        status, why = fetch(url, "HEAD")
        if status in (403, 405, 501) or (status is None and why not in ("DNS failure", "TLS failure")):
            status, why = fetch(url, "GET")
        if status is not None and status < 500 and status != 429:
            break
        if why in ("DNS failure", "TLS failure"):
            break
        time.sleep(2 * (attempt + 1))
    if status is not None and status < 400:
        return "ok", str(status)
    if status in DEAD_STATUS or why in ("DNS failure", "TLS failure"):
        return "dead", str(status) if status else why
    return "unknown", str(status) if status else why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="output")
    ap.add_argument("--report", default="")
    ap.add_argument("--section", default=PORTFOLIO)
    args = ap.parse_args()
    pages = pages_to_check(args.out, args.section)
    if not pages:
        print(f"external links: no page to check in {args.out} (is the build empty?)")
        return 2
    where = {}
    for page, links in pages.items():
        for link in links:
            where.setdefault(link, set()).add(page)
    results = {}
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
        for link, verdict in zip(where, pool.map(check, where), strict=True):
            results[link] = verdict
    dead = sorted((l, d) for l, (v, d) in results.items() if v == "dead")
    unknown = sorted((l, d) for l, (v, d) in results.items() if v == "unknown")
    ok = sum(1 for v, _ in results.values() if v == "ok")
    print(f"external links: {len(results)} checked on {len(pages)} pages: {ok} ok, {len(dead)} dead, {len(unknown)} could not check")
    for l, d in dead:
        print(f"  dead ({d}): {l}  on {', '.join(sorted(where[l]))}")
    pending = pending_media(args.out)
    print(f"pending media: {len(pending)}")
    for page, what, owner, url in pending:
        print(f"  {page}: {what}, in {owner} ({url})")
    if args.report:
        lines = [f"{len(results)} external links on {len(pages)} pages (the Portfolio and the main pages): "
                 f"{ok} ok, {len(dead)} dead, {len(unknown)} could not check.", ""]
        if dead:
            lines += ["## Dead", "", "| Page | Link | Status |", "|---|---|---|"]
            lines += [f"| {', '.join(sorted(where[l]))} | {l} | {d} |" for l, d in dead] + [""]
        if unknown:
            lines += ["## Could not check", "", "A site that blocks robots, a timeout or a server error. Check these by hand only if they stay here for months.", "",
                      "| Page | Link | Status |", "|---|---|---|"]
            lines += [f"| {', '.join(sorted(where[l]))} | {l} | {d} |" for l, d in unknown] + [""]
        if pending:
            lines += ["## Pending media", "", "Videos or audios that their owner has not published yet. When one is out, replace its note with the URL.", "",
                      "| Page | What | Where to look |", "|---|---|---|"]
            lines += [f"| {page} | {what} | [{owner}]({url}) |" for page, what, owner, url in pending] + [""]
        pathlib.Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
