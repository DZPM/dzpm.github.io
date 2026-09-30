# AGENTS.md

For coding agents. The [`README.md`](README.md) explains how the site works: how to add a post, the `make` targets, the checks, and what a push to `main` does (it is a release). Read it first, then:

- [`CONTEXT.md`](CONTEXT.md): the vocabulary (Post, Section, Kind, Cover, Archive, Redirect stub...). Use its words in code, docs, and commits.
- [`docs/adr/`](docs/adr/): the decisions. A change that goes against one needs a new ADR, not a quiet exception.
- [`docs/edge.md`](docs/edge.md): what lives outside the repository. A change in Cloudflare or DNS goes into it, in the same commit as its reason.

There is also a private repository that only the author can read. It was used to migrate 20 years of data, and it is out of the scope of this one: nothing here needs it, and nothing here names it or links to it.

## Before you call a change done

- Build with the production settings and run the checks on that build, not only `make build` and `make check`: CI fails on warnings.
- Run Pagefind as `python -m pagefind`; it is a Python package, not a binary on PATH.
- Do not push to `main` to see a change: that publishes it. Use `make serve`, or `make degrade` to see a page without its static files.

## Do not

- Edit the text of an Archive post (2006 to 2009), or of the comments and mentions JSON: they are a record (ADR 0007, ADR 0005). Remove, never rewrite.
- Add personal data, in content or in a fixture (ADR 0003). The PII gate stops it; do not weaken the gate to get past it.
- Add first-party JavaScript that a page needs to work, or JSON-LD (ADR 0004).
- Frame an origin that is not in `EMBED_ORIGINS` in `plugins/hst.py`, or edit the CSP by hand: it is generated from that list.
- Translate the content: the site is in Spanish. Code, comments, docs, ADRs, and commit messages are in English.
