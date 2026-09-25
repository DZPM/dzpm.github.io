# davidarcos.net

The personal site of David Arcos: a portfolio of talks and technical writing since 2012, and the archive of the personal blog that preceded it (2006 to 2009). Static, built with [Pelican](https://getpelican.com/), served by GitHub Pages.

- [`CONTEXT.md`](CONTEXT.md) is the domain glossary: the vocabulary of the site (Post, Section, Cover, Redirect stub, Legacy...), one meaning per word.
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

## Stack

| Concern | Choice |
|---|---|
| Generator | Pelican 4.12, Python 3.14, Markdown content, Jinja2 templates |
| Hosting | GitHub Pages, user site repository, custom domain `davidarcos.net` |
| Build and deploy | GitHub Actions ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)): build with fatal errors, index, gates, deploy |
| Search | [Pagefind](https://pagefind.app/), a static index built after Pelican; its script loads on the search page and the 404 page only |
| Edge | Cloudflare as DNS and proxy. Two redirect rules (the feed family, and `status` to the UptimeRobot page; `www` is redirected by GitHub Pages), nothing else outside the repository, all of it written down in [`docs/edge.md`](docs/edge.md) |
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
tools/                    the checks: the PII gate, the redirect stub check, the image metadata stripper
```

## Adding a post

1. Create `content/posts/YYYY-MM-DD-slug.md`:

   ```
   Title: Talk title
   Date: 2027-03-01 10:00
   Slug: talk-title
   Tags: Python, Slides, Video
   Summary: One sentence, in Spanish, for the card on the home page and the top of the post.
   Kind: charla
   Cover: talk-title.jpg

   The post, in Markdown.

   https://www.youtube.com/watch?v=VIDEOID
   ```

   The `Slug` is the address, `/blog/talk-title/`, and must be unique: the build fails on a collision. The `Kind` is one of charla, podcast, entrevista, mesa redonda, artículo. A short post that is neither a talk nor an article takes `Section: notes` instead of `Kind`, `Summary` and `Cover`: it is listed as a row on the Blog, under Notas, and never as a card. A video or a deck is embedded by putting its URL alone on a line (YouTube, Google Slides, SlideShare, Vimeo, Spreaker, Spotify).

2. Put the cover in `content/images/covers/talk-title.jpg`, under 300 KB and at least 1700 px wide (the column is 850 px, and screens are 2x), after `tools/strip_image_metadata.py`. The build makes the 480 px WebP card copy itself. The figures on Sobre el blog, in `llms.txt` and in `humans.txt` are counted by the build from the content (`{{ stats.posts }}` in a page becomes the number), so they never need editing.

3. `make build search`, look at it with `make serve`, commit, push to `main`. The workflow builds and deploys.

A post in progress carries `Status: draft` and a `Modified: YYYY-MM-DD` line records a later edit of a published one. A draft builds locally at `/borradores/<slug>/` and is never published; the modified date reaches the sitemap, the share metadata and the feed.

## Working locally

```
make setup      # venv, pinned dependencies, the pre-commit hook
make build      # pelican -> output/
make search     # pagefind index over output/
make serve      # http://127.0.0.1:8000
make check      # PII gate on the tree and the output, redirect stubs, internal links
```

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

The checks stayed here because they run on every commit and every deploy: `tools/pii_gate.py` refuses emails, IP addresses, long hex hashes, WordPress export fields and image metadata (pre-commit hook on staged files, whole tree, and the built output in CI); `tools/check_stubs.py` asserts every redirect stub points at a page that exists; `tools/check_links.py` asserts every link and image inside the site resolves; and the plugin refuses a build where a post has no Slug, a Portfolio post has no Summary or no Kind, a Section is unknown, or a cover is missing or over 300 KB.

## Licences

- Code (theme, plugin, tools, workflow): [GPL-3.0](LICENSE). The two fonts in `themes/hst/static/fonts/` are under the SIL Open Font License, copies alongside.
- David Arcos's texts, images and summaries: [CC BY-SA 4.0](LICENSE-CONTENT).
- Comments by other people are reproduced as published and remain their authors'. If a comment is yours and you want it gone, open an issue or send a message on LinkedIn or X: it is removed, no questions asked. Quoted talk abstracts and menéame titles belong to whoever wrote them. Photographs taken by other people, such as event photos used as covers, remain their authors' and are credited in the post.
