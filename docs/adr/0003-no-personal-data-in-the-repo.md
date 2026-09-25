---
status: accepted
---
# No personal data enters the repository

The repository is public and its history is permanent, so nothing that identifies a person beyond what the published site already showed may be committed. The WordPress export carries each Commenter's email address and IP address; those are used once, on the author's machine, to group Comments and to fetch an Avatar, and are then discarded. A Comment keeps its display name, website, date and body. Avatars are stored under opaque identifiers that cannot be traced back to an email. Raw exports, downloaded originals, conversion reports and the conversion scripts themselves live in a separate private repository, never in this one (docs/adr/0006): the scripts encode hand decisions about people and images (who is one person, what was blurred, which comment was reworded) that belong with the material, not in public. This repository keeps only the checks under `tools/`, which carry no data beyond the author's own address. A check runs over the repository and the built site before any push and blocks on any email or IP pattern.

Posts marked Legacy, kept away on purpose, follow the same rule as the raw material: they stay with it and never enter the repository, because a fifteen year old dead link can become a phishing or malware link once its domain is re-registered, and a public repository would keep serving it forever. They were kept out for their dead links or by the author's choice; a private list records them, because a public list of their addresses would be a map to their archived copies.

External links inside published Archive Posts carry a smaller version of the same risk. The Migration checks every one of them once, and a link whose domain no longer resolves or that answers with an error is unlinked, keeping its text, so the site never points readers at a re-registered domain.

The rule is about other people. The author's own email address appears in git metadata, in the license and in the Keybase proof, and is already public; it is the one address the checks allow.

## Consequences

- A Commenter who had a real photo on Gravatar keeps it, fetched once by hash on the author's machine; the hash itself is never written to the repository.
- Restoring a lost raw export means re-exporting from the WordPress backup, never from git.
