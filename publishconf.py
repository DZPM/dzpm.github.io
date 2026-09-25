"""Production overrides. Used by the GitHub Actions workflow: pelican -s publishconf.py"""

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *  # noqa: F401,F403

SITEURL = "https://davidarcos.net"
FEED_DOMAIN = SITEURL
RELATIVE_URLS = False
DELETE_OUTPUT_DIRECTORY = True
DRAFT_SAVE_AS = ""   # drafts never leave the machine
DRAFT_URL = ""
