---
name: blog-researcher
description: Deep technical web research and automated blog post generation. Researches official documentation, verifies architecture & code patterns, splits complex topics into multi-part series, adds cross-part navigation links, and outputs formatted Jekyll markdown posts in _posts/.
---

# Blog Researcher Skill

Use this skill whenever the user requests deep research on a technical topic or asks to generate detailed blog post(s) for the engineering blog.

---

## Workflow Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 1. Deep Search  │ ──►│ 2. Scope & Split│ ──►│ 3. Write Posts  │ ──►│ 4. Local Verify │
│    & Fact Check │    │    Evaluation   │    │    & Crosslink  │    │    (No Auto-Push│
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Step 1: Deep Web Research & Fact Verification

1. **Search Official Documentation**:
   - Use `search_web` to search for official documentation and high-authority technical sources (e.g. `go.dev`, `kafka.apache.org`, `docs.aws.amazon.com`, `kubernetes.io`, `rust-lang.org`).
   - Run multiple queries to cover architecture, internals, code syntax, edge cases, and production benchmarks.

2. **Verify Facts & Code Examples**:
   - Extract real, non-pseudocode examples.
   - Verify function signatures, flags, and configuration keys across official documentation.

---

## Step 2: Scope & Multi-Part Series Evaluation

Evaluate the depth and scope of the researched topic:

- **Single Post**: Select this if the topic is focused and can be thoroughly explained within a single 5-8 minute read (e.g., *"How Go's sync.Map Works"*).
- **Multi-Part Series**: Select this if the topic spans multiple major sub-domains (e.g., *"Building Resilient Kafka Pipelines: Architecture, Partitioning, and Failover"*).
  - Break the topic into logical parts (e.g., **Part 1: Core Concepts & Architecture**, **Part 2: Production Code & Patterns**, **Part 3: Performance & Troubleshooting**).
  - Assign separate filenames in `_posts/` with sequential dates or slugs:
    - `_posts/YYYY-MM-DD-topic-part-1.md`
    - `_posts/YYYY-MM-DD-topic-part-2.md`

---

## Step 3: Frontmatter & Formatting Standards

Every generated markdown post in `_posts/` MUST adhere to this exact YAML frontmatter structure:

```yaml
---
layout: post
title: "Topic Title: Subtitle (Part X)"
description: "A clear, 1-2 sentence technical summary of this article."
date: YYYY-MM-DD
categories:
  - PrimaryCategory
  - SecondaryCategory
tags:
  - tag1
  - tag2
author: "Saiteja Chada"
reading_time: "X min read"
draft: false
---
```

### Content & Style Guidelines
- **No Marketing Fluffy Intro**: Jump straight into the problem statement or technical background.
- **Header Hierarchy**: Use `##` for main sections and `###` for sub-sections. Do NOT use `#` H1 inside the body.
- **GitHub Alerts**: Use `> [!NOTE]`, `> [!TIP]`, or `> [!WARNING]` callouts for critical architecture tips.
- **Concrete Code Blocks**: Specify language tags (`go`, `typescript`, `bash`, `yaml`, `json`).
- **References Section**: End each post with a `## References` section listing official documentation links.

---

## Step 4: Multi-Part Series Cross-Linking

If writing a multi-part series, embed navigation banners into every part:

### Top Banner (place right below frontmatter):
```markdown
> [!NOTE]
> This article is **Part X of Y** in our in-depth series on **[Series Name]**.
> - **Part 1**: [Part 1 Title]({{ site.baseurl }}/topic-part-1/)
> - **Part 2**: [Part 2 Title]({{ site.baseurl }}/topic-part-2/)
```

### Bottom Navigation Bar (place right above References):
```markdown
---

| [← Previous: Part X-1]({{ site.baseurl }}/topic-part-prev/) | [Next: Part X+1 →]({{ site.baseurl }}/topic-part-next/) |
```

---

## Step 5: Local Verification & Git Safety

1. **Local Server Check**:
   - Confirm local dev server (`python scripts/blog/server.py`) is running on `http://localhost:5000/`.
   - Verify page rendering, TOC auto-generation, code block syntax highlighting, and series navigation links.

2. **Git Safety Rule**:
   - **Do NOT commit or push to Git automatically.**
   - Keep all newly generated files local and present the summary to the user.
   - Wait for the user's explicit command before pushing to remote.
