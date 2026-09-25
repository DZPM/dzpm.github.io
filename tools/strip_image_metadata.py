#!/usr/bin/env python3
"""Remove embedded metadata (EXIF, XMP, IPTC, text chunks) from images in place.

Run once on every image before it is committed. JPEG pixels are kept as
they are (no recompression); only the metadata segments are dropped.
Animated GIFs are left alone: re-encoding them would alter the artefact,
and a tool comment such as "Created with The GIMP" is not personal data.

Usage:  python tools/strip_image_metadata.py content/images/covers/*
"""

import os
import sys
import tempfile

from PIL import Image

META_KEYS = ("exif", "xmp", "photoshop", "comment")


def strip(path):
    with Image.open(path) as im:
        fmt = im.format
        had = [k for k in META_KEYS if im.info.get(k)]
        if fmt == "PNG":
            had += [k for k in getattr(im, "text", {}) if k.lower() != "gamma"]
        if fmt == "GIF":
            return fmt, [], "animated GIF left untouched" if getattr(im, "n_frames", 1) > 1 else "GIF left untouched"
        if not had:
            return fmt, [], "nothing to remove"
        im.load()
        for k in META_KEYS:
            im.info.pop(k, None)
        fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(path)[1], dir=os.path.dirname(path))
        os.close(fd)
        try:
            if fmt == "JPEG":
                # "keep" reuses the original quantization tables and subsampling: same pixels, no EXIF, no XMP.
                im.save(tmp, "JPEG", quality="keep", subsampling="keep", exif=b"", icc_profile=im.info.get("icc_profile"))
            elif fmt == "PNG":
                im.save(tmp, "PNG", optimize=True, icc_profile=im.info.get("icc_profile"))
            else:
                im.save(tmp, fmt)
        except Exception:
            os.unlink(tmp)
            raise
        os.replace(tmp, path)
        return fmt, had, "rewritten"


if __name__ == "__main__":
    for p in sys.argv[1:]:
        fmt, had, note = strip(p)
        print(f"{os.path.relpath(p)}: {fmt}, {note}" + (f", removed {had}" if had else ""))
