---
status: accepted
---
# Pelican on the GitHub Pages user site

The site leaves a WordPress install on a VPS running Ubuntu. It is built with Pelican, deployed to GitHub Pages by a GitHub Actions workflow, and lives in the user site repo `dzpm.github.io` with `davidarcos.net` as its custom domain. Pelican because it is Python: the author has more than twenty years of Python behind him and organises Python Barcelona, so the generator, its plugins and its templates are tools he already knows, and a bug in any of them is his to fix. The site's URL, tag, feed and comment needs are native to it. The user site repo, rather than a project repo, because a custom domain on the user site is inherited by every project repo of the account at `davidarcos.net/<repo>/`, which keeps room for other sites later without touching this one.

## Considered options

- Jekyll: the only generator GitHub Pages builds natively, rejected because it needs a Ruby toolchain the machine does not have, for a site whose author works in Python.
- Hugo and Eleventy: fine, and rejected only because Pelican fits the author better.
- Cloudflare Pages: solves redirects with a file in the repo, and was rejected to keep a single vendor in the deploy path. Cloudflare remains as DNS and proxy only.
