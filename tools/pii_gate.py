#!/usr/bin/env python3
"""Refuse personal data before it reaches the repository or the site.

Checks text files for email addresses, IP addresses, long hex hashes and
WordPress export fields, and images for embedded metadata. Runs on the
staged files (pre-commit), on the whole tree, or on the built site.

Usage:
  pii_gate.py --staged           files staged for commit (the pre-commit hook)
  pii_gate.py --tree             every tracked file
  pii_gate.py --output output    the built site, plus http:// asset URLs

Exit status 1 on any finding. See docs/adr/0003.
"""

import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The author's own address is the one exemption (docs/adr/0003).
ALLOWED_EMAILS = {"david.arcos@gmail.com"}

PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "obfuscated email": re.compile(r"\b[A-Za-z0-9._-]+\s*(?:(?:\(at\)|\[at\]|\bat\b)\s*[A-Za-z0-9.-]+\s*(?:\(dot\)|\[dot\]|\bdot\b|\(punto\)|\[punto\]|\bpunto\b)|(?:\(arrobah?\)|\[arrobah?\]|\barrobah?\b)\s*[A-Za-z0-9-]+\s*(?:\(dot\)|\[dot\]|\bdot\b|\(punto\)|\[punto\]|\bpunto\b|\.))\s*[A-Za-z]{2,}\b", re.I),   # "at" needs a spelled-out dot; "arroba" (Spanish) is unambiguous, a plain dot will do
    "ipv4": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
    # Full form (eight groups) or compressed form with at least three groups. Times of day (10:40:08) and CSS (a::after) match neither.
    "ipv6": re.compile(r"\b(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}\b|(?<![0-9a-f:])(?:(?:[0-9a-f]{1,4}:){1,6}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){1,6})(?![0-9a-f:])|(?<![0-9a-f:])(?:[0-9a-f]{1,4}:){2,6}:(?:[0-9a-f]{1,4})?(?![0-9a-f:])", re.I),
    "phone number": re.compile(r"\b(?:tel[eé]fono|tel|telf|tfno|fono|m[oó]vil|phone|ll[aá]mame|whatsapp)\b[^\n/]{0,12}?\+?\d[\d .-]{5,13}\d(?![\d/])|(?<![\d .-])(?:\d{3}[ .-]\d{3}[ .-]\d{3}|\d{3}[ .-]\d{2}[ .-]\d{2}[ .-]\d{2})(?![ .-]?\d)|(?<![\d.])(?:\+34[ .-]?)?[67]\d{8}(?![\d.])", re.I),   # a number called a phone, nine digits written like one (3-3-3 or 3-2-2-2), or a Spanish mobile run together
    "hex hash (32, 40 or 64)": re.compile(r"\b[0-9a-f]{32}\b|\b[0-9a-f]{40}\b|\b[0-9a-f]{64}\b", re.I),
    "gravatar": re.compile(r"gravatar\.com/avatar", re.I),
    "wordpress export field": re.compile(r"wp:author_email|wp:comment_author_email|wp:comment_author_IP|author_avatar_urls|X-Forwarded-For", re.I),
}

# Strings that look like findings but are not personal data.
ALLOWED_TEXT = {
    "185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153",  # GitHub Pages
    "2606:50c0:8000::153", "2606:50c0:8001::153", "2606:50c0:8002::153", "2606:50c0:8003::153",
    "0.0.0.0", "127.0.0.1",
    "22D488F46C908EDE33D383D7C77A3FF4B7FBAD91",   # the author's public GPG fingerprint, in security.txt
}
TEXT_EXT = {".md", ".html", ".xml", ".txt", ".py", ".yml", ".yaml", ".css", ".js", ".json", ".toml", ".cfg", ".csv", ".tsv", ".svg", ""}
# Paths whose content is made of hashes or is third party, checked by hand instead of by pattern.
ALLOWED_PATHS = (
    "tools/pii_gate.py",         # this file: the patterns and the allowlist live here
    ".well-known/keybase.txt",   # a signed proof, hashes by design
    "pagefind/",                 # Pagefind's own bundle carries its contributors' emails
    "theme/",                    # the theme's static files, ours, no text content
)
# Image comments written by tools, not people.
ALLOWED_IMAGE_COMMENTS = (b"Created with The GIMP", b"Created with GIMP", b"Lavc", b"Adobe", b"Picasa")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
SKIP_DIRS = {".git", ".venv", "node_modules", "output", "__pycache__"}


def tracked_files(staged):
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else ["git", "ls-files"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [os.path.join(ROOT, p) for p in out.split("\n") if p]


def output_files(directory):
    for base, dirs, files in os.walk(directory):
        for f in files:
            yield os.path.join(base, f)


def check_text(path, findings, http_assets=False):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return
    # SVG path data is a stream of numbers that looks like IP addresses. It is geometry, not text.
    # The feed carries the same HTML, escaped (&lt;svg ...&gt;), so its icons are blanked the same way.
    if path.endswith((".html", ".svg")):
        scan = re.sub(r"<svg\b.*?</svg>", lambda m: " " * len(m.group(0)), text, flags=re.S | re.I)
    elif path.endswith(".xml"):
        scan = re.sub(r"&lt;svg\b.*?&lt;/svg&gt;", lambda m: " " * len(m.group(0)), text, flags=re.S | re.I)
    else:
        scan = text
    # other people's words are rendered as HTML (a comment's body, a mention's excerpt), so markup that could run
    # must never enter: true of every archived file today, and it has to stay true if any are ever added
    if "/content/comments/" in path or "/content/mentions/" in path or path.startswith(("content/comments/", "content/mentions/")):
        for m in re.finditer(r"<\s*(script|iframe|form|object|embed|svg)\b|\\?[\"' ]on[a-z]+\s*=|javascript:|srcdoc=", scan, re.I):
            findings.append((path, text.count("\n", 0, m.start()) + 1, "active markup in archived text", m.group(0)[:40]))
    for name, rx in PATTERNS.items():
        if path.endswith("tools/pii_gate.py") and name in ("gravatar", "wordpress export field"):
            continue
        for m in rx.finditer(scan):
            hit = m.group(0)
            if name == "email" and hit.lower() in ALLOWED_EMAILS:
                continue
            if hit in ALLOWED_TEXT:
                continue
            if name == "hex hash (32, 40 or 64)" and (path.endswith((".woff", ".woff2")) or "/.github/workflows/" in path or path.startswith(".github/workflows/")):   # fonts are binary; the workflow pins its actions by commit hash
                continue
            line = text.count("\n", 0, m.start()) + 1
            findings.append((path, line, name, hit if name != "email" else hit.split("@")[0][:3] + "***@" + hit.split("@")[1]))
    if http_assets:
        # Mixed content is about what the page loads: src attributes and stylesheet links. A plain <a href> is not.
        for m in re.finditer(r'(?:\ssrc="(http://[^"]+)"|<link[^>]+href="(http://[^"]+)")', text):
            findings.append((path, text.count("\n", 0, m.start()) + 1, "http:// asset", m.group(1) or m.group(2)))


def check_image(path, findings):
    try:
        from PIL import Image
    except ImportError:
        findings.append((path, 0, "pillow missing, cannot check image metadata", ""))
        return
    try:
        with Image.open(path) as im:
            info = im.info
            for key in ("exif", "xmp", "photoshop", "comment"):
                if info.get(key):
                    if key == "comment" and any(info[key].startswith(t) for t in ALLOWED_IMAGE_COMMENTS):
                        continue
                    findings.append((path, 0, f"image metadata: {key}", f"{len(info[key])} bytes"))
            if im.format == "PNG":
                for k in im.text if hasattr(im, "text") else {}:
                    if k.lower() not in ("gamma",):
                        findings.append((path, 0, "png text chunk", k))
    except Exception as e:  # noqa: BLE001
        findings.append((path, 0, "unreadable image", str(e)[:80]))


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", action="store_true")
    g.add_argument("--tree", action="store_true")
    g.add_argument("--output", metavar="DIR")
    args = ap.parse_args()

    if args.output:
        files = list(output_files(os.path.join(ROOT, args.output)))
        http_assets = True
    else:
        files = tracked_files(args.staged)
        http_assets = False

    findings = []
    for path in files:
        rel = os.path.relpath(path, ROOT)
        if any(rel == d or rel.startswith(d + os.sep) for d in SKIP_DIRS) and not args.output:
            continue
        inner = os.path.relpath(path, os.path.join(ROOT, args.output)) if args.output else rel.split(os.sep, 1)[-1] if rel.startswith("content" + os.sep) else rel
        if any(inner == a or inner.startswith(a) for a in ALLOWED_PATHS) or any(rel.endswith(a) for a in ALLOWED_PATHS if not a.endswith("/")):
            continue
        if re.fullmatch(r"[0-9a-f]{32}\.txt", os.path.basename(path)):
            continue   # the IndexNow key file at the root: a 32 hex character name and body, public by design (tools/indexnow.py)
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXT:
            check_image(path, findings)
        elif ext in TEXT_EXT or os.path.basename(path) in ("LICENSE", "LICENSE-CONTENT", "CNAME"):
            check_text(path, findings, http_assets=http_assets and ext == ".html")

    if findings:
        print(f"PII gate: {len(findings)} finding(s)")
        for path, line, name, hit in findings:
            print(f"  {os.path.relpath(path, ROOT)}:{line}  {name}  {hit}")
        return 1
    print(f"PII gate: clean ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
