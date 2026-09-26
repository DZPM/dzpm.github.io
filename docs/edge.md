# The edge: what lives outside the repository

Everything that serves the site and is not in this repository, written down so it can be checked and rebuilt. The zone is checked against this file with snapshots taken through the Cloudflare API with a scoped, short-lived token kept outside the repositories. Decisions behind it: docs/adr/0001 (GitHub Pages behind Cloudflare), docs/adr/0002 (redirects), docs/adr/0004 (no HTML rewriting at the edge). Kept current: a change here is a change to this file in the same commit as the reason.

## Registrar and nameservers

| Item | Value |
|---|---|
| Registrar | NameCheap, registrar only, auto renew on, registrar lock on |
| Nameservers | Cloudflare (`dawn.ns.cloudflare.com`, `jack.ns.cloudflare.com`) |
| Mail | none: the domain has no MX and receives no mail |
| DNSSEC | on since 2026-09-26: Cloudflare signs the zone (algorithm 13, key tag 2371) and the DS record is at NameCheap. Checked with `https://dns.google/resolve?name=davidarcos.net&type=DNSKEY`, which must answer `"AD": true`. To turn it off, delete the DS at NameCheap first, wait a day, then disable it in Cloudflare: the other order breaks resolution for every validating resolver |

## DNS records at Cloudflare

The apex and `www` are proxied (orange cloud), decided 2026-09-21: the proxy is what makes the redirect rules work, and the one day the author's ISP blocked Cloudflare's range (2026-09-15) was the ISP's problem with half the web, not this site's.

| Name | Type | Value | Proxy |
|---|---|---|---|
| `davidarcos.net` | A | `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` | proxied |
| `davidarcos.net` | AAAA | `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153` | proxied |
| `www` | CNAME | `dzpm.github.io` | proxied |
| `_github-pages-challenge-dzpm` | TXT | the value GitHub shows when the domain is added to the account's verified domains (Settings, Pages; created 2026-09-26). Keep it: with the domain verified, no other GitHub account can claim `davidarcos.net` or a subdomain for its own Pages site | DNS only |
| `davidarcos.net` | TXT | `google-site-verification=…` (the Search Console domain property, 2026-09-26; keep it, Google checks it again from time to time) | DNS only |
| `status` | AAAA | `100::` (a placeholder: the host exists only for the Status redirect rule below) | proxied |
| `davidarcos.net` | CAA | `0 issue "letsencrypt.org"` (the origin certificate, issued to GitHub Pages) and `0 issue "pki.goog"` (the edge certificate, Google Trust Services) | DNS only |

Nothing else. The two CAA records were checked against the live issuers before they were created (2026-09-26). Cloudflare publishes more CAA records than these two: once a zone has any, it adds the authorities its Universal SSL may use (Sectigo, DigiCert, SSL.com, with `issuewild`), so that the edge certificate always renews. Every other authority stays out. `www` is redirected to the apex by GitHub Pages, not by a rule. `status` points at nobody on purpose: a CNAME to a third party's host is a takeover waiting to happen the day the service is dropped, so the redirect is a rule and the record a placeholder. The old `s` record (a CNAME to a statistics service the author no longer uses) was removed on 2026-09-21, before the cutover. The dormant DNS zone at DigitalOcean goes when the droplet does, a month after the cutover: a subdomain pointing at a service nobody controls is a takeover waiting to happen.

## GitHub Pages

- Repository `DZPM/dzpm.github.io`, user site, deployed by the workflow in `.github/workflows/deploy.yml` from `main`.
- Custom domain `davidarcos.net`, set in the repository settings and by the `CNAME` file in `content/extra/` (served at the root). Enforce HTTPS: on.
- The `CNAME` file enters the repository only at the cutover: with it present, GitHub serves the site only at the custom domain and redirects `dzpm.github.io` there, so the first deploy is tested at `dzpm.github.io` without it. The same file decides the address the site is built for: `publishconf.py` reads `content/extra/CNAME` and falls back to `https://dzpm.github.io`, so the staging deploy is a working site and not a set of pages pointing at the old server.

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
| HSTS (SSL/TLS, Edge Certificates) | on: `max-age` one year, `includeSubDomains`, no preload, `nosniff` on | sets `Strict-Transport-Security` and `X-Content-Type-Options`; see Response headers |
| Brotli | on | harmless |
| Browser Cache TTL | Respect Existing Headers | GitHub Pages sends `max-age=600`; a reader sees a change within ten minutes, and the stylesheet carries the commit hash in its URL anyway |
| Caching level | standard or aggressive | HTML is not cached at the edge either way (`cf-cache-status: DYNAMIC`); only the static files are |

## Redirect rules

Two rules. "Status", since 2026-09-21: when `http.host eq "status.davidarcos.net"`, redirect to `https://stats.uptimerobot.com/4Jmwltz8Nq`, status 302 (temporary, because the page's identifier belongs to UptimeRobot and its free plan allows no custom domain), preserve nothing. If the status page is ever deleted, the rule and the `status` record go the same day.

"Feeds", created at the cutover, a single redirect, status 301, preserve nothing:

- When: the path ends in any of the eight feed addresses WordPress served, written as a chain of `or`, because the free plan does not allow the regular expression operator (`matches` needs a Business plan):

  ```
  ends_with(http.request.uri.path, "/feed") or ends_with(http.request.uri.path, "/feed/") or
  ends_with(http.request.uri.path, "/feed/atom") or ends_with(http.request.uri.path, "/feed/atom/") or
  ends_with(http.request.uri.path, "/feed/rss") or ends_with(http.request.uri.path, "/feed/rss/") or
  ends_with(http.request.uri.path, "/feed/rss2") or ends_with(http.request.uri.path, "/feed/rss2/")
  ```

- Then: redirect to `https://davidarcos.net/blog/feed.xml`, status 301, query string dropped.

It covers `/feed/`, `/blog/feed/`, `/blog/feed/atom/`, `/blog/comments/feed/`, `/blog/category/<x>/feed/` and the comment feed of every post, `/blog/YYYY/MM/DD/<slug>/feed/`: every one of them ends in one of the eight strings above. Feed readers do not follow the HTML meta refresh of a redirect stub, which is why this one lives at the edge; `/feed/` and `/blog/feed/` also have a stub in the site, for a browser, in case the proxy is ever off. The comment feeds matter to nobody (no comments since 2013): if the rule is ever lost, only the two post feed addresses are worth anything.

## Cache rules

GitHub Pages sends `max-age=600` on every file. Two **Cache Rules** keep the static files longer (Rules, Cache Rules; created in the dashboard, the token has no Cache Rules permission):

| Name | Expression | Edge TTL | Browser TTL |
|---|---|---|---|
| `Theme assets, one year` | `starts_with(http.request.uri.path, "/theme/")` | one year, ignore the origin | one year, override the origin |
| `Images, one week` | `starts_with(http.request.uri.path, "/images/")` | one month, ignore the origin | one week, override the origin |

A year is safe for `/theme/` only because every address under it that a page loads changes when its file changes: `style.css` and the scripts carry the commit (`ASSET_VERSION`), and the fonts and the theme images carry a hash of their content (`ASSET_HASH` in `pelicanconf.py`; the plugin gives the stylesheet's `url()` the same hash, so the preloaded font and the one the stylesheet asks for are one download). A new file under `/theme/` must be loaded the same way, or a change to it stays in the readers' browsers for a year. `/images/` gets a week and not a year because a post's image is sometimes replaced under the same name (a new crop); to show a replaced image at once, purge its address. `/pagefind/` has no rule: `pagefind.js` has no version in its address.

## Response headers

GitHub Pages sends no security headers and a `<meta>` CSP cannot set `frame-ancestors`, so Cloudflare sets them, on every response (redirects included). Two sources, since 2026-09-26:

| Header | Value | Source |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (the `status` host is HTTPS through the proxy, so the subdomains clause holds; no preload, which is hard to undo) | HSTS setting |
| `X-Content-Type-Options` | `nosniff` | HSTS setting |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | rule |
| `X-Frame-Options` | `DENY` | rule |
| `Content-Security-Policy` | `frame-ancestors 'none'` (the page's own CSP in the `<meta>` stays; this one adds the directive a meta cannot carry) | rule |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` (only features every browser knows: an unknown one, such as the retired `interest-cohort`, fills the console with warnings) | rule |
| `Cross-Origin-Opener-Policy` | `same-origin` | rule |

"HSTS setting" is the zone setting in the table above. "Rule" is one **Response Header Transform** rule named "Security headers" (Rules, Transform Rules, Modify Response Header, all incoming requests, each header with "Set static"). The **Managed Transform** "Add security headers" stays off: it sets other values (`X-Frame-Options: SAMEORIGIN`) and neither `frame-ancestors` nor COOP. No `Cross-Origin-Embedder-Policy`: it would block the YouTube and Spotify embeds.

The rule is created in the dashboard: the scoped token has no Transform Rules permission and gets 403 on that phase, even to read it. Headers are not HTML: docs/adr/0004 forbids rewriting the page, and a header leaves it untouched. `nosniff` holds because every script and stylesheet has the right type (`application/javascript`, `text/css`); the Pagefind index and WASM are fetched as data, which `nosniff` does not check. Check all seven with:

    curl -sI https://davidarcos.net/ | grep -iE 'strict-transport|nosniff|referrer|frame|permissions|opener'

## Cutover, in order

The cutover ran on 2026-09-26, from 00:20 to 00:40 (Barcelona): the domain now serves the static site, the old server is kept, powered off, as the way back (step 7).

1. Push `main`; the workflow deploys to `https://dzpm.github.io/`. Test there: search (the Content-Security-Policy), fonts, a redirect stub, the feed, a tag page, a shared link preview.
2. Add `content/extra/CNAME` (one line, `davidarcos.net`) and the domain in the Pages settings; add the TXT record GitHub asks for.
3. Turn Development Mode on (the edge stops caching for three hours). Change the apex A and AAAA records from the old server to the GitHub addresses above, and `www` to the CNAME, all with the proxy off (grey cloud) and TTL 1 minute, so a way back propagates in a minute. From this moment until step 4 completes, `https://davidarcos.net/` answers with GitHub's own certificate (a name mismatch) and a browser shows a warning: the gap lasts the minutes, at most an hour, that Pages takes to issue the certificate. Do it at a quiet hour and do not announce the site until step 6.
4. Wait for Pages to show the certificate as active; turn on Enforce HTTPS.
5. Proxy on (orange cloud) for the apex and `www`, TTL back to Auto; SSL mode to Full (strict); create the Feeds rule (the Status rule already exists); confirm the five settings above are off and the minimum TLS is 1.2.
6. Purge Everything (Caching, Configuration) and Development Mode off. Checks: `https://davidarcos.net/.well-known/keybase.txt`, `.../.well-known/security.txt`, `/sitemap.xml`, `/blog/feed.xml` and `/blog/feed/` (301), a menéame link (`/blog/2007/11/09/free-krusher/`), `www.davidarcos.net` (301 to the apex), a search, a post with no `<script>` other than `theme/js/theme.js` and no `cdn-cgi` in its HTML, `make indexnow`, the sitemap in Search Console and Bing Webmaster Tools, the Keybase proof re-signed.
7. The old server is kept for a month as the way back, powered off since 2026-09-26; then it is destroyed and its DNS zone at DigitalOcean with it. **The way back**, in this order: power the droplet on (a minute), then the apex A record back to the old server's address (kept with the migration notes, not in this repository), `www` CNAME to `davidarcos.net`, proxy on, **SSL mode to Flexible** (the droplet serves HTTPS with a self-signed certificate, so Full (strict) would answer 526), delete the Feeds rule, purge. Five minutes.
8. Sixty days after step 4, check that GitHub renewed the certificate (`echo | openssl s_client -connect davidarcos.net:443 -servername davidarcos.net 2>/dev/null | openssl x509 -noout -dates` while the records are proxied shows Cloudflare's edge certificate; the origin's is checked in the Pages settings, which say "Certificate active" and its expiry). If Pages cannot renew behind the proxy, the fix is to set the records to grey for the renewal and back.

## Monitoring

UptimeRobot, the author's free account, two monitors on `https://davidarcos.net/`, alerts by email:

- **The old monitor**, HTTP(s), kept: it watched `/blog/` since the WordPress years and was moved to `/` on 2026-09-26. It keeps its history and two options new monitors on this account no longer offer (Check SSL Errors, a 10 second timeout). It watched the address, not the old server, so the cutover did not break it and destroying the server will not either. This is the monitor on the status page.
- **A keyword monitor**, added 2026-09-26: alerts when `Hic sunt trolls` is missing from the page, every 5 minutes. It catches the one failure the first cannot see, a page that answers 200 but is not this site (a parked domain, a wrong deploy). The phrase is in the `<title>` of `/`: if the home title changes, change the keyword. The public status page is UptimeRobot's, reached through `https://status.davidarcos.net/`. No analytics.
