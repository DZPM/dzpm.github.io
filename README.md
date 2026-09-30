# davidarcos.net

The personal site of David Arcos: a portfolio of talks and technical writing since 2012, and the archive of the personal blog that preceded it (2006 to 2009). Static, built with [Pelican](https://getpelican.com/), served by GitHub Pages.

- [`CONTEXT.md`](CONTEXT.md) is the domain glossary: the vocabulary of the site (Post, Section, Cover, Redirect stub, Legacy...), one meaning per word.
- [`AGENTS.md`](AGENTS.md) is for coding agents: how to verify a change, what a push does, and the rules the code does not show.
- [`docs/adr/`](docs/adr/) holds the Architecture Decision Records: the decisions that are hard to reverse, each with its context and its consequences.

| ADR | Decision | In one line |
|---|---|---|
| [0001](docs/adr/0001-pelican-on-the-github-pages-user-site.md) | Pelican on the GitHub Pages user site | Python the author can fix, a static host with no server to keep, `davidarcos.net` as the custom domain |
| [0002](docs/adr/0002-post-address-is-blog-slug.md) | A Post's address is `/blog/<slug>/` | No dates in the address; every old WordPress address gets a redirect stub, the feeds a rule at the edge |
| [0003](docs/adr/0003-no-personal-data-in-the-repo.md) | No personal data enters the repository | Emails and IPs are used once on the author's machine and discarded; a check refuses them on every commit |
| [0004](docs/adr/0004-no-first-party-javascript-on-content-pages.md) | No first party JavaScript that a page depends on | Search needs its script, the theme switch enhances; a script may never carry a page or call out |
| [0005](docs/adr/0005-comment-authors-are-normalised-per-person.md) | Comment authors are normalised per person | One display name and site per person, grouped by Gravatar hash and merged by hand; the text stays as published |
| [0006](docs/adr/0006-two-repositories-the-site-and-how-it-was-made.md) | Two repositories: the site, and how it was made | The public one builds the site; the private one holds the exports, the scripts and the hand decisions |
| [0007](docs/adr/0007-the-archive-is-preserved-and-pruned-only-by-removal.md) | The Archive is preserved, and pruned only by removal | Nothing in a 2006 to 2009 Post is rewritten; what cannot stay is removed, and the record of it stays private |
| [0008](docs/adr/0008-comments-are-closed.md) | Comments are closed | No form, no widget; the 463 old Comments are a record, and a Commenter can ask for theirs to go |
| [0009](docs/adr/0009-the-section-is-a-date-the-kind-a-word-and-notes-the-third-lane.md) | The Section is a date, the Kind a word, and Notes are the third lane | Portfolio and Archive by date, Notes by front matter for new short posts; the Kind is one of five words |
| [0010](docs/adr/0010-html-at-the-edge-purged-on-deploy.md) | The HTML is cached at the edge for a week and purged on every deploy | The deploy purges Cloudflare and fails unless the edge serves the new commit; a purge-only token in the deploy environment |
| [0011](docs/adr/0011-every-page-shares-a-generated-card.md) | Every post and page shares a designed image | A Portfolio post shares its cover (a small one on a blurred copy of itself), the rest a 1200x630 card the build draws; CARD_VERSION forces a refetch |

## Stack

| Concern | Choice |
|---|---|
| Generator | Pelican 4.12, Python 3.14, Markdown content, Jinja2 templates |
| Hosting | GitHub Pages, user site repository, custom domain `davidarcos.net` |
| Build and deploy | GitHub Actions ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)): build with fatal errors, index, gates, deploy |
| Search | [Pagefind](https://pagefind.app/), a static index built after Pelican; its script loads on the search page and the 404 page only |
| Edge | Cloudflare as DNS and proxy: redirect rules (the feed family, and `status` to the UptimeRobot page; `www` is redirected by GitHub Pages), the security headers, and the cache rules (the HTML is cached for a week and purged on every deploy, ADR 0010). All of it is written down in [`docs/edge.md`](docs/edge.md) |
| Theme | `themes/hst`, three layouts, one CSS file, light and dark through `light-dark()` (the reader's browser by default, or the switch in the header, the one script on every page), no icon font, no framework. Two fonts served from the theme (Inter for the text and the titles, Fira Code for numbers and code, both OFL, latin subsets, no italic face: an emphasis is a medium weight), with the system font behind them |

Content pages depend on no first-party JavaScript (ADR 0004): the theme switch enhances them, the search page needs its script. Embeds are plain `<iframe>` elements generated at build time from a bare URL on its own line.

## Layout

```
content/posts/            one post per file, YYYY-MM-DD-slug.md, Pelican metadata header
content/pages/            inicio.md (the home page), sobre-el-blog.md, and the hidden trolls, wp-admin and mapa-wardley
content/images/covers/    one image per portfolio post, named after the slug
content/images/posts/     the Archive photos restored on purpose, one folder per post
content/images/avatars/   the frozen set of comment avatars produced by the migration
content/comments/         one JSON file per post with comments, produced by the migration
content/mentions/         one JSON file per post with pingbacks or trackbacks, produced by the migration
content/extra/            files served as they are: favicon, robots.txt, the Keybase proof, files/
themes/hst/               the theme: templates, icons as inline SVG, style.css
plugins/hst.py            embeds, section and cover derivation, redirect stubs, comment and mention loading, the years and the tag names in a text marked and linked at build time
tools/                    the checks: the PII gate, the redirect stub check, the image metadata stripper; the edge purge the deploy runs; and the monthly external link check
```

## Adding a post

1. Create `content/posts/YYYY-MM-DD-slug.md`:

   ```
   Title: Talk title
   Date: 2027-03-01 10:00
   Slug: talk-title
   Tags: Python, Slides, Video
   Summary: One sentence, in Spanish, for the card on the home page and the top of the post. It is also the description that search engines and shared links show: 100 to 155 characters.
   Kind: charla
   Cover: talk-title.jpg

   The post, in Markdown.

   https://www.youtube.com/watch?v=VIDEOID
   ```

   The `Slug` is the address, `/blog/talk-title/`, and must be unique: the build fails on a collision. The `Kind` is one of charla, podcast, entrevista, mesa redonda, artículo. A short post that is neither a talk nor an article takes `Section: notes` instead of `Kind`, `Summary` and `Cover`: it is listed as a row on the Blog, under Notas, and never as a card. A video or a deck is embedded by putting its URL alone on a line (YouTube, Google Slides, SlideShare, Vimeo, Spreaker, Spotify). For SlideShare and Spreaker, use the address of their embed player (`/embed_code/...`, `/embed/...`). Any other URL alone on a line stays a plain link. A video or an audio that is not there takes a line in its place: `Pendiente: el vídeo de la charla, en [el YouTube de CPS Spain](https://www.youtube.com/@cpsspain).` when its owner has not published it yet, or `Retirado: el vídeo de la charla, en [el Vimeo de NoSQL matters](https://vimeo.com/52213638).` when its owner took it down. Both show a box the size of a player; the monthly link report lists the pending ones. The build draws the post's share card, the 1200x630 image a shared link shows (docs/adr/0011): there is nothing to do for it. `tools/check_meta.py` fails the build when a page lacks its card or its share tags, or when the description of a talk, an article or a page is under 100 or over 160 characters; for a note and for the Archive it only warns (a note may take a `Summary` to set its description). To embed a new provider, add its origin to `EMBED_ORIGINS` in `plugins/hst.py` and its branch in `embed_html`: the CSP of every page takes its `frame-src` from that list, and `tools/check_csp.py` fails the build if a page frames an origin its CSP does not allow.

2. Put the cover in `content/images/covers/talk-title.jpg`, under 300 KB and at least 1700 px wide (the column is 850 px, and screens are 2x), after `tools/strip_image_metadata.py`. The build makes the 480 px WebP card copy itself. The cover is also what a shared link to the post shows (docs/adr/0011): about 1600x1000 (16:10) is best, with what matters in the central band that a 1.91:1 crop keeps; a cover under 1200 px is shared as a 1200x630 copy the build draws, the cover over a blurred copy of itself. The figures on Sobre el blog, in `llms.txt` and in `humans.txt` are counted by the build from the content (`{{ stats.posts }}` in a page becomes the number), so they never need editing.

3. `make build search`, look at it with `make serve`, commit, push to `main`. The workflow builds and deploys.

A post in progress carries `Status: draft` and a `Modified: YYYY-MM-DD` line records a later edit of a published one: a change to what it says, not to its style or markup. A draft builds locally at `/borradores/<slug>/` and is never published; the modified date reaches the sitemap, the share metadata and the feed.

In a post or a page, a bold number alone (`**100** ms`) renders as a figure, in the mono face and not bold; `**100 ms**` stays bold text. When the design of the share cards changes, raise `CARD_VERSION` in `pelicanconf.py`: platforms keep an image by its address, so a new address is the only way to make them fetch it again (docs/adr/0011).

## Working locally

```
make setup      # venv, pinned dependencies, the pre-commit hook
make build      # pelican -> output/
make search     # pagefind index over output/
make serve      # http://127.0.0.1:8000
make degrade    # http://127.0.0.1:8001 with the static files off: pages only (see tools/serve.py for --allow-images, --no-images, --no-js)
make check      # PII gate on the tree and the output, redirect stubs, internal links
```

`make build` is lenient (`--fatal errors`); the workflow builds with `publishconf.py` and `--fatal warnings`, so a warning that passes locally fails the deploy. Before a push, build the production settings into a separate directory (`pelican content -o <dir> -s publishconf.py --fatal warnings`, then `python -m pagefind --site <dir>`) and run the checks on it. Every check fails on an empty build.

A push to `main` is a release: the workflow builds, runs the checks, deploys to GitHub Pages, purges the Cloudflare cache, and fails unless the edge serves the new commit (docs/adr/0010). A pull request builds and checks, and deploys nothing. `main` refuses force pushes and deletion.

The dependencies are pinned with a hash for every file. Edit `requirements.in`, then regenerate `requirements.txt` with the `pip-compile` command in its header. Pygments stays below 2.20 because Pelican requires it. Dependabot proposes updates once they are a week old.

## Initial migration

The site was migrated in September 2026 from a WordPress install on an Ubuntu VPS, with [Claude Code](https://claude.com/claude-code). This repository holds the result: the content, the theme and the checks. The raw material and the conversion scripts live in a private repository, because the exports carry other people's email addresses and IP addresses, the server copies carry its configuration, and the scripts encode the hand decisions of the migration (which photos to restore, which comments to merge under one person, what to blur). Nothing in there is needed to build or change the site.

What the migration did, in order:

1. **Pulled** posts, comments and tags from the WordPress REST API, and later the database dump, the WXR export and the uploads tree from the server itself.
2. **Converted** each post from HTML to Markdown with a deliberately small vocabulary, one report per post listing every change that alters visible structure. Dates were corrected to the event where the post was published late, nine posts were kept out as Legacy (ADR 0003), menéame front pages were recorded, and WordPress's curly punctuation went back to plain characters.
3. **Checked every external link** once. Dead means unresolvable, timed out, 404/410/5xx, or redirected to a different domain (a re-registered domain looks exactly like that); dead links keep their text and lose the link. A denylist covers domains known to have changed hands.
4. **Grouped the commenters** by Gravatar hash, never by email, gave each person an opaque id, fetched the real photos with `d=404` and drew identicons for the rest, normalised names and sites per person (ADR 0005), and wrote one JSON file per post with name, site, date and body. Emails and IPs were used on the author's machine and discarded (ADR 0003).
5. **Restored the Archive photos** on purpose, post by post, from the Flickr dump and the server's uploads: at most 1200 px, JPEG 82, no metadata, a face or an address blurred where needed. The Archive ships text only except for that list.
6. **Read the pingbacks and trackbacks** out of the database dump into one JSON file per post ("Menciones"), approved only, no self-pings, each URL checked with the link rules.
7. **Generated the redirect stubs** (ADR 0002) for every old address shape: the dated permalinks with and without `/blog/`, date archives, the category, pagination, and tag pages, which land on the static tag pages.

Once a month, `.github/workflows/links.yml` runs `tools/check_external_links.py` (`make links` locally) over the Portfolio posts and the main pages, not the archive, whose dead links are shown as dead on purpose. A link is dead only on 404, 410, a DNS failure or a TLS failure; a site that blocks robots is "could not check". The dead ones go to one issue labelled `links`, which the next clean run closes.

The checks stayed here because they run on every commit and every deploy: `tools/pii_gate.py` refuses emails, IP addresses, long hex hashes, WordPress export fields and image metadata (pre-commit hook on staged files, whole tree, and the built output in CI); `tools/check_stubs.py` asserts every redirect stub points at a page that exists; `tools/check_links.py` asserts every link and image inside the site resolves; and the plugin refuses a build where a post has no Slug, a Portfolio post has no Summary or no Kind, a Section is unknown, or a cover is missing or over 300 KB; and the gate refuses active markup (a script, an iframe, an event handler) inside the archived comments and mentions, which are rendered as HTML.

## Licences

- Code (theme, plugin, tools, workflow): [GPL-3.0](LICENSE). The two fonts in `themes/hst/static/fonts/` are under the SIL Open Font License, copies alongside.
- David Arcos's texts, images and summaries: [CC BY-SA 4.0](LICENSE-CONTENT).
- Comments by other people are reproduced as published and remain their authors'. If a comment is yours and you want it gone, open an issue or send a message on LinkedIn or X: it is removed, no questions asked. Quoted talk abstracts and menéame titles belong to whoever wrote them. Photographs taken by other people, such as event photos used as covers, remain their authors' and are credited in the post.
