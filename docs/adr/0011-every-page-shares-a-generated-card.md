---
status: accepted
---
# Every post and page shares a card the build draws

A shared link shows an image, and the image is often all a reader sees. Before this decision, a post shared its cover, or the first photo of its text, or the generic `og.png`: 57 of 138 posts shared `og.png`, 66 an image narrower than the 1,200 px the platforms ask for (22 narrower than 600 px), and 15 a proper one. The build now draws a 1200x630 card for every post and page with Pillow: the author and the blog at the top, the title, the kind and the date (a page shows its summary instead), the domain, and the post's cover as a panel on the right when it has one. The home keeps `og.png`, the designed card of the whole site.

Three options were weighed:

| Option | Result | Cost |
|---|---|---|
| Share the cover or `og.png` (before) | one post in nine had a good card | none |
| Replace the small covers by hand | only the posts someone reworks improve, and the next post can regress | hand work per post |
| **Draw a card per page at build time** | every page, and every future post, shares a designed card with no step | a few seconds of build, a few MB of output |

## Consequences

- The cards are never committed: `write_og_cards` in `plugins/hst.py` draws them into `output/images/og/`. Their file name carries a hash of what they show (title, kind, date, summary, the cover's bytes, the design version `OG_DESIGN`), so a changed title gives a new address and LinkedIn, X and WhatsApp fetch the new card instead of their cached copy. A change to the layout bumps `OG_DESIGN`.
- A card with a photo is a JPEG, a card with text only a PNG: whichever is smaller for what it holds. The whole set is about 7 MB for 143 cards.
- The covers stay as they are: the card crops the cover into its panel, so a cover needs no fixed size. A cover narrower than the panel (500 px) looks soft in it; that is the only reason to replace one.
- `tools/check_meta.py` fails the build when a page lacks its card or its image metadata, so the cards cannot silently stop.
