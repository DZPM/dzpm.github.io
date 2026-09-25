---
status: accepted
---
# Comment authors are normalised per person

A Comment's text is preserved exactly as published (docs/adr/0003), but its author line is not: the same person commented under several names, sites and email addresses between 2006 and 2013, and showing them as different people would misrepresent the conversation. Identities are grouped by email during the Migration (through the Gravatar hash, never an address), and merged by hand only where the name is distinctive and the site matches. Per person, the name shown is the one used last, the site is the latest one still working, and the Avatar is the latest real photo. The name as signed stays in the comment file and is never rendered. Sixteen merges cover thirty-nine identities, found by hand and by a pass over the export (same address at two providers, same nickname, same network in a short window); the rest are single.

## Consequences

- A joke pseudonym on one comment renders as the person's usual name.
- Re-running the Migration reproduces the same result from the same opaque ids; no email is needed.
