---
status: accepted
---
# A Post's address is `/blog/<slug>/`

WordPress addressed posts as `/blog/YYYY/MM/DD/slug/`. The new site drops the date segments: all 138 slugs are unique (133 migrated, one recovered from a 2006 revision, the new ones), the date belongs on the page, and a scheme with fewer parts is the one least likely to need another migration. `/blog/` stays as the namespace for Posts because the user site serves sibling repos at `davidarcos.net/<repo>/`, and Posts at the root would claim every future path. Every Original URL, in both its `/blog/...` and its older no-`/blog/` form, is served by a Redirect stub generated inside the site, rather than by rules at the CDN, so the redirects travel with the repo and can be tested locally.

One kind of address cannot be served by a stub and is handled at Cloudflare, which stays in front of the site as DNS and proxy: the feed family (`/blog/feed/`, `/blog/feed/atom/`, `/feed/`, the category feeds, the per post comment feeds), because feed readers do not follow HTML meta refresh. One redirect rule sends every one of them to the site's one Atom feed. `www.davidarcos.net` needs no rule: with `www` pointed at GitHub Pages, GitHub itself redirects it to the apex. That rule, the DNS records and the proxy settings are the only configuration that lives outside the repository; they work only while the records stay proxied, and they are written down, verbatim, in `docs/edge.md`.

## Consequences

- A Redirect stub is a meta refresh with a canonical link, not an HTTP 301. Search engines treat it as a redirect; the few inbound links that matter, mostly menéame stories from 2006 and 2007, keep working.
- A new Post must choose a Slug that no other Post has. The build fails on a collision, because Pelican refuses to write the same output file twice and the build runs with fatal errors.
- Addresses with a query string, such as the `?p=NNN` shortlinks WordPress advertised, cannot be stubbed and land on `/blog/` silently. Accepted.
