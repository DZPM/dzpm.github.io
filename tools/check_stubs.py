#!/usr/bin/env python3
"""Assert every redirect stub in the built site points at a page that exists.

Usage:  python tools/check_stubs.py output
"""

import os
import re
import sys

REFRESH = re.compile(r'http-equiv="refresh" content="0; url=([^"]+)"')


def main(out):
    stubs = 0
    bad = []
    for base, _dirs, files in os.walk(out):
        for f in files:
            if f != "index.html":
                continue
            path = os.path.join(base, f)
            text = open(path, encoding="utf-8").read(2000)
            m = REFRESH.search(text)
            if not m:
                continue
            stubs += 1
            target = m.group(1)
            rel = re.sub(r"^https?://[^/]+", "", target).split("?", 1)[0].split("#", 1)[0].strip("/")
            # a target is a page (a directory with its index.html) or a file (the feed)
            if not os.path.exists(os.path.join(out, rel, "index.html")) and not os.path.isfile(os.path.join(out, rel)):
                bad.append((os.path.relpath(path, out), target))
    if bad:
        print(f"{len(bad)} stub(s) point nowhere:")
        for p, t in bad:
            print(f"  {p} -> {t}")
        return 1
    print(f"stubs: {stubs}, all targets exist")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "output"))
