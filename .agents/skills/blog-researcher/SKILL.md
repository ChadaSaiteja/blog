---
name: blog-researcher
description: Deep technical web research and automated blog post generation. Researches official documentation, verifies architecture & code patterns, splits complex topics into multi-part series, and outputs Jekyll markdown posts in _posts/ that conform to _data/blog_style.yml.
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

## Step 3: Post Structure — read the config, do not improvise

**`_data/blog_style.yml` is the single source of truth for post style.** It defines the
design tokens, the cover/figure treatment, the front matter key order, the section
skeleton, the heading rules, the callout syntax and the quality rubric. Do not restate
any of it from memory and do not hardcode values from this file — if the config and
this document disagree, the config wins.

Scaffold instead of writing front matter by hand:

```bash
python scripts/blog/new_post.py "How Redis Streams Actually Work" \
  --categories Backend,DistributedSystems --tags redis,streams
python scripts/blog/new_post.py "Some Topic" --print   # preview, writes nothing
```

That emits front matter in the exact key order declared in
`structure.frontmatter_order`, with defaults from `structure.defaults` and a section
skeleton built from `structure.sections`.

The rules that matter most when writing the body:

- **No marketing intro.** Jump straight into the problem statement or background.
- **Heading hierarchy** — `##` for sections, `###` for sub-sections. Never `#`; the
  layout owns the single `h1`. `structure.rules` holds the bounds.
- **Callouts** — `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!IMPORTANT]`,
  `> [!CAUTION]`. `assets/js/main.js` promotes these to styled callouts and strips
  the marker, so the syntax must be exactly `> [!MARKER]`.
- **Code blocks** — always tag the language (`go`, `typescript`, `bash`, `json`,
  `text`). The language label in the code box header is read from that tag.
- **Diagrams** — mermaid, fenced as ```` ```mermaid ````, is the diagram language.
  No committed SVG or image files; `images.diagrams.rules` in the config has the
  house conventions.
- **Categories** must come from `structure.category_enum`. `validate_style.py` and
  `quality.py` both fail a post that uses anything else, and the listing filter
  tabs and cover colours are both derived from that list.
- **End with `## References`** listing official documentation and primary sources.

---

## Step 4: Multi-Part Series Cross-Linking

Give every part a `series:` front matter key naming the series. The layout renders it
as a note above the author card, and `page.previous` / `page.next` supply the
automatic Previous / Next navigation, so the only thing a series needs from you is
the `series:` value.

---

## Step 5: Local Verification & Git Safety

1. **Validate before anything else** — this is the same gate CI runs:
   ```bash
   python scripts/blog/validate_style.py _posts/YYYY-MM-DD-topic.md
   python scripts/blog/quality.py _posts/YYYY-MM-DD-topic.md
   ```
   `validate_style.py` checks structure (front matter order, enum, headings,
   callouts). `quality.py` scores editorial quality against the rubric in the config
   and must clear `rubric.gate` (80).

2. **Local Server Check**:
   - Confirm the dev server (`python scripts/blog/server.py`) is running on
     `http://localhost:5000/`.
   - Verify rendering, the table of contents, code box language labels, callouts and
     the cover tile. The dev server renders the real layouts against the real
     config via `scripts/blog/liquid_render.py`; if it cannot resolve a construct it
     prints a banner at the top of the page rather than silently dropping markup.
   - Note: Pygments token classes differ slightly from Rouge's, so preview syntax
     colours are close to but not identical with the deployed site.

3. **Git Safety Rule**:
   - **Do NOT commit or push to Git automatically.**
   - Keep all newly generated files local and present the summary to the user.
   - Wait for the user's explicit command before pushing to remote.
