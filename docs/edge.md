# The edge: what lives outside the repository

Everything that serves the site and is not in this repository, written down so it can be checked and rebuilt. The zone is checked against this file with snapshots taken through the Cloudflare API with a scoped, short-lived token kept outside the repositories. Decisions behind it: docs/adr/0001 (GitHub Pages behind Cloudflare), docs/adr/0002 (redirects), docs/adr/0004 (no HTML rewriting at the edge). Kept current: a change here is a change to this file in the same commit as the reason.

## Registrar and nameservers

| Item | Value |
|---|---|
| Registrar | NameCheap, registrar only, auto renew on, registrar lock on |
| Nameservers | Cloudflare (`dawn.ns.cloudflare.com`, `jack.ns.cloudflare.com`) |
| Mail | none: the domain has no MX and receives no mail |

## DNS records at Cloudflare

The apex and `www` are proxied (orange cloud), decided 2026-09-21: the proxy is what makes the redirect rules work, and the one day the author's ISP blocked Cloudflare's range (2026-09-15) was the ISP's problem with half the web, not this site's.

| Name | Type | Value | Proxy |
|---|---|---|---|
| `davidarcos.net` | A | `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` | proxied |
| `davidarcos.net` | AAAA | `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153` | proxied |
| `www` | CNAME | `dzpm.github.io` | proxied |
| `_github-pages-challenge-dzpm` | TXT | the value GitHub shows when the domain is added to Pages | DNS only |
| `status` | AAAA | `100::` (a placeholder: the host exists only for the Status redirect rule below) | proxied |

Nothing else. `www` is redirected to the apex by GitHub Pages, not by a rule. `status` points at nobody on purpose: a CNAME to a third party's host is a takeover waiting to happen the day the service is dropped, so the redirect is a rule and the record a placeholder. The old `s` record (a CNAME to a statistics service the author no longer uses) was removed on 2026-09-21, before the cutover. The dormant DNS zone at DigitalOcean goes when the droplet does, a month after the cutover: a subdomain pointing at a service nobody controls is a takeover waiting to happen.

## GitHub Pages

- Repository `DZPM/dzpm.github.io`, user site, deployed by the workflow in `.github/workflows/deploy.yml` from `main`.
- Custom domain `davidarcos.net`, set in the repository settings and by the `CNAME` file in `content/extra/` (served at the root). Enforce HTTPS: on.
- The `CNAME` file enters the repository only at the cutover: with it present, GitHub serves the site only at the custom domain and redirects `dzpm.github.io` there, so the first deploy is tested at `dzpm.github.io` without it.

## Cloudflare settings

| Setting | Value | Why |
|---|---|---|
| SSL/TLS mode | Full (strict) | GitHub Pages serves HTTPS with a valid certificate; Flexible would loop |
| Always Use HTTPS | on | |
| Rocket Loader | off | docs/adr/0004: nothing rewrites the HTML |
| Email Address Obfuscation | off | same |
| Auto Minify | off | same |
| Web Analytics automatic setup | off | same; zone analytics (server side) are the only analytics allowed |
| Automatic HTTPS Rewrites | off | same: it rewrites `http://` links in the HTML; the site's own links are already https |
| Minimum TLS version | 1.2 | a static site in 2026 has no reader on TLS 1.0 or 1.1 |
| Brotli | on | harmless |
| Browser Cache TTL | Respect Existing Headers | GitHub Pages sends `max-age=600`; a reader sees a change within ten minutes, and the stylesheet carries the commit hash in its URL anyway |
| Caching level | standard or aggressive | HTML is not cached at the edge either way (`cf-cache-status: DYNAMIC`); only the static files are |

## Redirect rules

Two rules. "Status", since 2026-09-21: when `http.host eq "status.davidarcos.net"`, redirect to `https://stats.uptimerobot.com/4Jmwltz8Nq`, status 302 (temporary, because the page's identifier belongs to UptimeRobot and its free plan allows no custom domain), preserve nothing. If the status page is ever deleted, the rule and the `status` record go the same day.

"Feeds", created at the cutover, a single redirect, status 301, preserve nothing:

- When: the request path matches the regular expression `^(/blog)?(/.*)?/feed(/atom|/rss2?)?/?$` (Cloudflare Rules language: `http.request.uri.path matches "..."`).
- Then: redirect to `https://davidarcos.net/blog/feed.xml`.

It covers `/feed/`, `/blog/feed/`, `/blog/feed/atom/`, `/blog/comments/feed/`, `/blog/category/<x>/feed/` and the comment feed of every post, `/blog/YYYY/MM/DD/<slug>/feed/`. Feed readers do not follow the HTML meta refresh of a redirect stub, which is why this one lives at the edge; `/feed/` and `/blog/feed/` also have a stub in the site, for a browser, in case the proxy is ever off. The comment feeds matter to nobody (no comments since 2013): if the rule is ever lost, only the two post feed addresses are worth anything.

## Response headers

GitHub Pages sends no security headers and a `<meta>` CSP cannot set `frame-ancestors`, so one **Response Header Transform** rule at Cloudflare ("Headers", Rules, Transform Rules, Modify Response Header, all requests) sets, on every response:

| Header | Value |
|---|---|
| `Strict-Transport-Security` | `max-age=86400` the first week, then `max-age=31536000; includeSubDomains` (the `status` host is HTTPS through the proxy, so the subdomains clause holds) |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | `frame-ancestors 'none'` (the page's own CSP in the `<meta>` stays; this one adds the directive a meta cannot carry) |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), interest-cohort=()` |
| `Cross-Origin-Opener-Policy` | `same-origin` |

Headers are not HTML: docs/adr/0004 forbids rewriting the page, and a header leaves it untouched. Created in the week after the cutover, and checked with `curl -sI https://davidarcos.net/ | grep -i strict-transport`.

## Cutover, in order

1. Push `main`; the workflow deploys to `https://dzpm.github.io/`. Test there: search (the Content-Security-Policy), fonts, a redirect stub, the feed, a tag page, a shared link preview.
2. Add `content/extra/CNAME` (one line, `davidarcos.net`) and the domain in the Pages settings; add the TXT record GitHub asks for.
3. Turn Development Mode on (the edge stops caching for three hours). Change the apex A and AAAA records from the old server to the GitHub addresses above, and `www` to the CNAME, all with the proxy off (grey cloud) and TTL 1 minute, so a way back propagates in a minute. From this moment until step 4 completes, `https://davidarcos.net/` answers with GitHub's own certificate (a name mismatch) and a browser shows a warning: the gap lasts the minutes, at most an hour, that Pages takes to issue the certificate. Do it at a quiet hour and do not announce the site until step 6.
4. Wait for Pages to show the certificate as active; turn on Enforce HTTPS.
5. Proxy on (orange cloud) for the apex and `www`, TTL back to Auto; SSL mode to Full (strict); create the Feeds rule (the Status rule already exists); confirm the five settings above are off and the minimum TLS is 1.2.
6. Purge Everything (Caching, Configuration) and Development Mode off. Checks: `https://davidarcos.net/.well-known/keybase.txt`, `.../.well-known/security.txt`, `/sitemap.xml`, `/blog/feed.xml` and `/blog/feed/` (301), a menéame link (`/blog/2007/11/09/free-krusher/`), `www.davidarcos.net` (301 to the apex), a search, a post with no `<script>` other than `theme/js/theme.js` and no `cdn-cgi` in its HTML, `make indexnow`, the sitemap in Search Console and Bing Webmaster Tools, the Keybase proof re-signed.
7. The old server stays on, untouched, for a month as the way back; then it is destroyed and its DNS zone at DigitalOcean with it. **The way back**, in this order: the apex A record to the droplet's address (in `docs/cloudflare-access.md`, the baseline snapshot), `www` CNAME to `davidarcos.net`, proxy on, **SSL mode to Flexible** (the droplet serves HTTPS with a self-signed certificate, so Full (strict) would answer 526), delete the Feeds rule, purge. Five minutes.
8. Sixty days after step 4, check that GitHub renewed the certificate (`echo | openssl s_client -connect davidarcos.net:443 -servername davidarcos.net 2>/dev/null | openssl x509 -noout -dates` while the records are proxied shows Cloudflare's edge certificate; the origin's is checked in the Pages settings, which say "Certificate active" and its expiry). If Pages cannot renew behind the proxy, the fix is to set the records to grey for the renewal and back.

## Monitoring

UptimeRobot, the author's free account, one monitor for the site: HTTPS to `https://davidarcos.net/`, keyword `Hic sunt trolls` present, every 5 minutes, alerts by email. At the cutover the author creates this monitor new and deletes the old one (which watched `/blog/` on the old server); the status page then shows the new one. The public status page is UptimeRobot's, reached through `https://status.davidarcos.net/`. No analytics.
