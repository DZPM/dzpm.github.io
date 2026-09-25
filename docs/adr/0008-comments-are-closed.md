---
status: accepted
---
# Comments are closed

The site takes no new Comments: no form, no third party widget, no email-to-comment. The 463 Comments it shows were written on the WordPress site between 2006 and 2013 and are kept as a record (docs/adr/0003, 0005, 0007). Comments were closed there in 2013 and stay closed here, for now; if they ever open again, that is a decision for that day, and it will not be through a third party service.

The reason is the cost of keeping them, which is not technical. A comment system means moderation, every day, for as long as the site exists: the old site's queue held, next to the spam, insults, attacks and threats that its readers never saw because the author read them first. A static site with no comments has no queue. The reader who wants to say something has the author's public profiles, linked from every page, and the repository's issues for anything about the site itself.

## Considered options

- A hosted widget (Disqus, giscus, Commento): rejected twice over, by docs/adr/0004 (a script on every Post) and by docs/adr/0003 (a third party holding readers' data).
- Webmentions: the closest to the old pingbacks, and rejected for the same moderation cost with a smaller audience.
- Comments by email or by pull request: possible without a script, and not wanted for now.
