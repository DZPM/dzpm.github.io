"""Production overrides. Used by the GitHub Actions workflow: pelican -s publishconf.py"""

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *  # noqa: F401,F403

# The address the site is built for. Until the cutover the deploy lives at the Pages address, so the domain comes from
# content/extra/CNAME: the file GitHub Pages reads to serve the custom domain is the same file that switches the build.
# No CNAME, no custom domain: everything is built for dzpm.github.io and the staging deploy works as a site, not as a
# set of pages pointing at the old server (docs/edge.md, step 2).
_cname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "extra", "CNAME")
SITEURL = "https://" + open(_cname).read().strip() if os.path.exists(_cname) else "https://dzpm.github.io"
FEED_DOMAIN = SITEURL
RELATIVE_URLS = False
DELETE_OUTPUT_DIRECTORY = True
DRAFT_SAVE_AS = ""   # drafts never leave the machine
DRAFT_URL = ""
