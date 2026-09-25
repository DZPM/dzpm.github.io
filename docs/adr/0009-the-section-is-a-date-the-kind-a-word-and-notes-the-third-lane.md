---
status: accepted
---
# The Section is a date, the Kind a word, and Notes are the third lane

Every Post belongs to one Section. For a migrated Post the Section is decided by its date and nothing else: before 2012 it is Archive, from 2012 on it is Portfolio. A Post written new can declare `Section: notes` in its front matter and become a Note: a short piece that is neither a talk nor an article, listed as a row on the Blog under Notas, never as a card on the Home, with no Cover and no Summary required. The build refuses `Section:` on a Post dated before 2012.

A Portfolio Post also carries a Kind, one word from a closed list (charla, podcast, entrevista, mesa redonda, artículo), shown with its emoji before the date on the card and at the top of the Post ("Artículo del 18 de septiembre de 2026"). The build refuses a Portfolio Post without a Kind, or with a Kind outside the list.

The date rule exists to protect the Archive (docs/adr/0007): if the Section could be written by hand, an Archive Post could be promoted to a card by editing one line, and the promise that the personal era is kept as a record, under its Banner, would depend on nobody ever doing that. The third lane exists because without it the site could not be written on: with two Sections decided by date, every new Post is a Portfolio Post, and a Portfolio Post must have a cover image and a hand-written Summary and lands as a talk on the Home. A yearly review, a note of two hundred words or a rant would have had to dress as a talk or not exist.

The Kind is a word and not a Tag because it answers a different question. A Tag says what a Post is about and a Post can have many; the Kind says what a Post *is* and there is exactly one. Keeping the list closed keeps the emoji and the wording consistent across the site, and the lint keeps a new Post from inventing a sixth.

## Considered options

- A `Section:` allowed on every Post, date as the default: rejected, it makes docs/adr/0007 a convention instead of a rule.
- Kind as a Tag ("Charla", "Podcast"): rejected, it mixes the two questions, and the tag index would show them as topics.
- No third lane, and new short posts as Portfolio without a cover: rejected, the Home would fill with cards that are not talks, and the lint would have to allow a Portfolio Post without a cover for everyone.
- A fourth Section for yearly reviews or other kinds of new writing: not needed; a Note is any new Post that is not a talk or an article, and a Kind can be added to Notes later if a distinction is ever wanted.

## Consequences

- `plugins/hst.py` derives the Section from the date unless the front matter says `notes`; `Section:` on a Post before 2012 fails the build.
- `CONTEXT.md` defines Section, Portfolio, Archive, Notes and Kind. The README shows the front matter of a talk and of a Note.
- The Blog lists the Portfolio as cards, then the Notes as rows under their own heading, then the Archive. The Home shows the Portfolio only.
- Adding a Kind means one entry in the plugin's list and its emoji; nothing else changes.
