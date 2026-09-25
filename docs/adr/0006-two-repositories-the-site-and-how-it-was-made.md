---
status: accepted
---
# Two repositories: the site, and how it was made

This public repository holds what is needed to build and check the site, and nothing else: the content, the theme, the plugin, the build configuration and the checks under `tools/`. Everything the Migration used and decided lives in a second, private repository: the raw exports, the copies taken off the old server, the conversion scripts, the hand decisions (which identities are one person, which comments were kept out or reworded, what was blurred and where, which Posts are Legacy), the local proofreading pages, and the working history of this repository before its first push, as bundles. The private repository is never named in public. The rule for what may enter here is one question: is it needed to build or check the site? If not, it stays with the Migration material.

The split exists for three reasons that no single check covers. The exports carry other people's addresses (docs/adr/0003). The scripts encode editorial decisions about people and about the author, which are his to keep, not to publish. And the code of the conversion is not what the site is about: a reader of this repository should find a site, not a project.

The Migration is finished. This repository is the only source of truth for everything on the site: a change to a Post, a Comment file, a photo or a page is made here, reviewed here, and never by regenerating from the material. The scripts in the private repository may still be run to check (the yearly pass over external links) or to redo one derived file from its original (a new blur on a photo already published); what they produce enters here as an ordinary change, never as a regeneration in bulk.

## Consequences

- The private repository is hosted on GitHub as a private repository, with the same data that lived for thirteen years on a rented server and today lives in a synced folder; private hosting does not worsen that, and it keeps a history. It carries a warning at the top of its README and push protection on, and is never forked or made public.
- Issues and pull requests are welcome here for typos, dead links and the like. A Commenter who wants a Comment of theirs removed only has to ask, through an issue or a message on LinkedIn or X, and it is removed without discussion.
- The decision tables in the private repository (merges, omissions, edits) are the final record of the Migration, not a living mechanism; a later change to a Comment is made in its file here, and the table is not updated to match.
