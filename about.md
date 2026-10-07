---
layout: page
title: "About"
seo_title: "About Saiteja Chada | Saiteja's Dev Blog"
description: "Who writes Saiteja's Dev Blog, what it covers, and how to get in touch. Backend engineering notes on distributed systems, data structures, and developer tooling."
permalink: /about/
---

I am **Saiteja Chada**, a backend engineer working on distributed systems and
developer tooling. This site is where I write down the things I had to work out
the hard way, in enough detail that I would not have to work them out again.

## What this blog covers

The through-line is **backend systems and the tooling around them**. In practice
that means four overlapping clusters:

- **Distributed systems.** How Google stores petabytes on unreliable hardware,
  and why chunking plus replication plus heartbeats is the whole trick.
- **Data structures at scale.** Counting billions of unique users in 12 KB with
  HyperLogLog, and knowing when *not* to reach for it.
- **Backend and security design.** OAuth 2.0 with PKCE done properly, webhook
  ingestion, rate limiting, token handling, and system design walkthroughs.
- **AI-assisted development tooling.** How to keep an AI coding agent inside
  your architecture instead of inventing a new one every prompt.

The bias throughout is **mechanism over marketing**. If a post says something is
fast or reliable, it explains the structure that makes it so, and names the
trade-off that comes with it.

## How the writing works

Every technical post here follows the same shape, and it is deliberate:

1. A short definition of the concept in the first few paragraphs, so the page is
   useful to someone who just landed from search and has no context.
2. The mechanism, with real numbers and real code.
3. An explicit trade-offs section, because every technique has a cost.
4. Links to primary sources &mdash; official documentation and specifications,
   never an aggregator.

Posts are written with the assumption that the reader is competent but has not
worked on this specific system before.

## Get in touch

- **GitHub** &mdash; [github.com/chadasaiteja](https://github.com/chadasaiteja)
- **LinkedIn** &mdash; [linkedin.com/in/chada-saiteja](https://www.linkedin.com/in/chada-saiteja/)

Found a mistake, or a post that drifted out of date? Corrections are welcome and
the fastest route is the
[issue tracker](https://github.com/ChadaSaiteja/blog/issues) or a pull request
against the post's Markdown file.

## Elsewhere on this site

- [All articles]({{ site.baseurl }}/) &mdash; the full archive, newest first.
- [RSS feed]({{ site.baseurl }}/feed.xml) &mdash; every new post as it publishes.
