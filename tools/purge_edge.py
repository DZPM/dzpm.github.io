#!/usr/bin/env python3
"""Purge the Cloudflare cache after a deploy, and prove the edge serves the new build (docs/adr/0010).

Every page carries the commit it was built from, in the address of its stylesheet (`style.css?v=<short hash>`).
The tool reads that value from the home page to know which build a server holds.

Steps:
  1. Origin: ask GitHub Pages directly (its four addresses, name davidarcos.net, certificate checked), not
     through Cloudflare, until the home page carries the commit. Only then is a purge safe: a purge while
     GitHub still serves the old build would let Cloudflare keep the old page for its whole edge TTL.
  2. Purge: remove every file of the zone from Cloudflare's cache (purge_everything). The token and the zone id
     come from the environment: CLOUDFLARE_PURGE_TOKEN, CLOUDFLARE_ZONE_ID.
  3. Edge: ask through Cloudflare until the home page carries the commit; purge once more after 60 s of stale
     answers. Then print cf-cache-status (HIT, MISS or DYNAMIC) for information.

Usage:
  python3 tools/purge_edge.py --commit <sha>            all three steps (the deploy job)
  python3 tools/purge_edge.py --commit <sha> --check    steps 1 and 3, no purge, no token
  --timeout <s> sets the origin wait (default 300); the edge wait is 180 s, or the same value if smaller.

Exit codes: 0 the edge serves the commit; 2 the origin never served it; 3 the purge failed (no token or
zone id, or the API refused); 4 the edge never served it; 5 bad arguments.

Standard library only: the deploy runner installs nothing.
"""
import argparse
import http.client
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request

HOST = "davidarcos.net"
ORIGIN_ADDRESSES = ("185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153")   # GitHub Pages
BUILD = re.compile(r"style\.css\?v=([0-9a-f]+)")
POLL = 10   # seconds between two tries


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def build_of(html):
    m = BUILD.search(html)
    return m.group(1) if m else None


def from_origin():
    """The home page as GitHub Pages serves it, from the first of its addresses that answers."""
    ctx = ssl.create_default_context()   # checks the certificate against HOST, not against the address
    for ip in ORIGIN_ADDRESSES:
        try:
            conn = http.client.HTTPSConnection(HOST, 443, timeout=20, context=ctx)
            conn.sock = ctx.wrap_socket(socket.create_connection((ip, 443), timeout=20), server_hostname=HOST)   # this address, this name
            conn.request("GET", "/", headers={"Host": HOST, "User-Agent": "purge_edge", "Cache-Control": "no-cache"})
            r = conn.getresponse()
            body = r.read().decode("utf-8", "replace")
            conn.close()
            if r.status == 200:
                return body
            log(f"origin {ip}: HTTP {r.status}")
        except (OSError, ssl.SSLError, http.client.HTTPException) as e:
            log(f"origin {ip}: {e}")
    return None


def from_edge():
    """The home page and its cf-cache-status, through Cloudflare."""
    req = urllib.request.Request(f"https://{HOST}/", headers={"User-Agent": "purge_edge"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace"), r.headers.get("cf-cache-status", "-")


def purge():
    token, zone = os.environ.get("CLOUDFLARE_PURGE_TOKEN"), os.environ.get("CLOUDFLARE_ZONE_ID")
    if not token or not zone:
        log("purge: CLOUDFLARE_PURGE_TOKEN or CLOUDFLARE_ZONE_ID is not set")
        sys.exit(3)
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/zones/{zone}/purge_cache",
        data=json.dumps({"purge_everything": True}).encode(), method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            answer = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            answer = json.load(e)
        except ValueError:
            answer = {"success": False, "errors": [f"HTTP {e.code}"]}
    if not answer.get("success"):
        log(f"purge: refused: {answer.get('errors')}")   # the error list only; the token is never printed
        sys.exit(3)
    log("purge: done (purge_everything)")


def wait(what, fetch, commit, limit, on_stale=None):
    """Poll fetch() until the page carries the commit, or give up after limit seconds."""
    start, seen, stale_hook_done = time.monotonic(), None, False
    while True:
        html = fetch()
        seen = build_of(html) if html else None
        if seen and commit.startswith(seen):
            log(f"{what}: serves {seen}")
            return True
        elapsed = time.monotonic() - start
        if on_stale and not stale_hook_done and elapsed >= 60:
            on_stale()
            stale_hook_done = True
        if elapsed >= limit:
            log(f"{what}: still serves {seen or 'nothing readable'} after {int(elapsed)} s, want {commit[:7]}")
            return False
        log(f"{what}: serves {seen or 'nothing readable'}, want {commit[:7]}; next try in {POLL} s")
        time.sleep(POLL)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", required=True, help="the full commit hash of the build that was deployed")
    ap.add_argument("--check", action="store_true", help="wait for the origin and check the edge; do not purge")
    ap.add_argument("--timeout", type=int, default=300, help="seconds to wait for the origin (default 300)")
    try:
        args = ap.parse_args()
    except SystemExit:
        sys.exit(5)
    commit = args.commit.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        log(f"bad --commit: {args.commit!r}")
        sys.exit(5)

    log(f"step 1: wait for GitHub Pages to serve {commit[:7]}")
    if not wait("origin", from_origin, commit, args.timeout):
        sys.exit(2)
    if not args.check:
        log("step 2: purge the Cloudflare cache")
        purge()
    log("step 3: wait for Cloudflare to serve the same build")
    edge_html = lambda: from_edge()[0]
    if not wait("edge", edge_html, commit, min(180, args.timeout), on_stale=None if args.check else purge):
        sys.exit(4)
    log(f"edge: cf-cache-status {from_edge()[1]} (HIT only once the HTML cache rule exists)")


if __name__ == "__main__":
    main()
