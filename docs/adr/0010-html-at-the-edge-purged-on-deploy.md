---
status: accepted
---
# The HTML is cached at the edge for a week and purged on every deploy

Cloudflare keeps every response of the site for a week, the HTML too, and the deploy workflow empties that cache as soon as GitHub Pages serves the new build. Before, only `/theme/` and `/images/` were cached at the edge: every page view went to GitHub Pages (`cf-cache-status: DYNAMIC`), about 200 ms from the monitor, where a cached page answers from the nearest Cloudflare site.

A purge that nobody checks is a stale site waiting to happen, so the purge proves itself. `tools/purge_edge.py` reads the build from the home page (the stylesheet address carries the commit), waits until GitHub Pages serves this commit (asked directly, not through Cloudflare: a purge while GitHub still serves the old build would let the edge keep the old page for the whole week), purges, then waits until Cloudflare serves the same commit. If the edge never does, the deploy fails and the owner gets the mail.

Three options were weighed:

| Option | After a deploy | Speed | Cost |
|---|---|---|---|
| No HTML at the edge (before) | new at once | every view goes to GitHub | none |
| A short edge TTL, ten minutes, no purge | up to ten minutes old | fast only within those ten minutes | none |
| **A week at the edge, a checked purge on deploy** | new at once, and checked | fast for every view | one token, one workflow step |

## Consequences

- A Cloudflare API token with one permission, Zone, Cache Purge, Purge, on this zone only, lives as the secret `CLOUDFLARE_PURGE_TOKEN` of the `github-pages` environment, next to the variable `CLOUDFLARE_ZONE_ID`. The environment only takes deploys from `main`, so a pull request or a Dependabot run never sees it. If it leaks, it can only empty the cache: revoke it and make another.
- The purge is `purge_everything`: a template change touches about 1,400 files, and a purge by address takes 30 at a time on this plan. The assets are versioned, so the edge refills at little cost.
- A failed purge makes the deploy red and leaves the previous build at the edge: old, not broken. The fixes are to run the job again, `make edge` (the same checks without a purge), or a purge from the Cloudflare dashboard.
- The cache rule is made in the dashboard after the first deploy that runs the purge, so nothing is cached for a week before a purge exists (`docs/edge.md`, Cache rules).
