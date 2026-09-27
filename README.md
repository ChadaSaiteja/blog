# Saiteja's Dev Blog

A personal engineering blog built with a custom **Flask dev server** + **Jekyll-style static rendering**. Posts are written in Markdown with YAML frontmatter and optionally generated with AI tooling.

Live at → [chadasaiteja.github.io/blog](https://chadasaiteja.github.io/blog)

---

## Stack

| Layer | Tech |
|---|---|
| Posts | Markdown + YAML frontmatter |
| Dev Server | Python / Flask |
| Rendering | Custom Markdown → HTML pipeline |
| Styling | Vanilla CSS (Inter + JetBrains Mono) |
| AI Tooling | OpenAI / Anthropic (optional) |
| Publishing | GitHub API (PR-based) |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/chadasaiteja/blog.git
cd blog
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

```env
# Choose your AI provider: 'openai' or 'anthropic'
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini

# API Keys (only the one matching your provider is required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# GitHub — only needed for publishing via PR
GITHUB_TOKEN=ghp_...
GITHUB_OWNER=chadasaiteja
GITHUB_REPOSITORY=chadasaiteja.github.io
```

### 4. Start the dev server

```bash
python scripts/blog/server.py
```

The blog will be available at **http://localhost:5000**

The dev server is not a mock. It reads the real `_config.yml`, the real
`_data/blog_style.yml` and the real `_layouts/` and `_includes/` templates, and
renders them through `scripts/blog/liquid_render.py`, so the preview matches the
deployed structure. Two known differences:

- Pygments token classes do not match Rouge's one for one, so syntax colours are
  close to but not identical with the deployed site. The markup around them is
  identical, which is what the code box chrome and language labels depend on.
- If the renderer meets a Liquid construct it does not support, it prints a
  banner at the top of the page naming the construct instead of quietly dropping
  the markup.

---

## Writing a Post

### `_data/blog_style.yml` is the single source of truth

Every post's appearance and structure is defined in **`_data/blog_style.yml`**.
It holds the design tokens (colours, fonts, spacing, the code-block palette and
the callout tints), the cover/figure treatment, the front matter key order, the
section skeleton, the heading and callout rules, and the quality rubric.

Four consumers read it, and nothing about post style is defined anywhere else:

| Consumer | What it does |
|---|---|
| `_includes/tokens.html` | Emits the tokens as `:root` CSS custom properties |
| `_includes/cover-tile.html` | Builds the deterministic 16:9 cover from the slug + category |
| `scripts/blog/new_post.py` | Scaffolds a new post from the declared shape |
| `scripts/blog/quality.py` | Scores against the rubric and gate in the config |

Change a colour once in that file and the whole site follows. The same values
are duplicated in `assets/css/main.css` as a **fallback only** — if the data
file is ever removed the site still renders correctly.

### Scaffold rather than hand-writing front matter

```bash
python scripts/blog/new_post.py "How Redis Streams Actually Work" \
  --categories Backend,DistributedSystems --tags redis,streams

python scripts/blog/new_post.py "Some Topic" --print   # preview, writes nothing
```

This writes `_posts/YYYY-MM-DD-how-redis-streams-actually-work.md` with front
matter in the exact key order from `structure.frontmatter_order`, defaults
applied, and a section skeleton built from `structure.sections`.

### Frontmatter

```yaml
---
layout: post
title: "Your Post Title"
description: "A one-line summary shown in cards and meta tags."
date: 2026-08-10
categories:
  - Backend
tags:
  - golang
author: "Saiteja Chada"
reading_time: "5 min read"
draft: false
---
```

| Field | Required | Notes |
|---|---|---|
| `title` | ✅ | Shown in cards, page title, and `<h1>` |
| `description` | ✅ | Card excerpt + meta description; 50–160 characters |
| `date` | ✅ | `YYYY-MM-DD`; must match the filename date |
| `categories` | ✅ | Must be in `structure.category_enum`; drives the filter tabs and cover colour |
| `tags` | optional | Shown as badges |
| `author` | optional | Falls back to `author_profile.name` in the config |
| `reading_time` | optional | Falls back to `structure.defaults.reading_time` |
| `series` | optional | Names the series; renders a note above the author card |
| `draft` | optional | `true` hides the post from the listing |

### Then write your content in Markdown

```markdown
Opening paragraph, no heading. State the problem in the first sentence.

## The Problem

Paragraph text here...

> [!NOTE]
> Callouts use GitHub Alerts syntax and are styled automatically.

### Sub-heading

- Bullet one
- Bullet two

\```typescript
const example = "code blocks get a language label and a copy button";
\```

\```mermaid
flowchart LR
    A[Client] --> B[Broker]
\```

## Key Takeaways

- One thing worth remembering.

## References

1. [Official documentation](https://example.com/real)
```

The rules, all defined in the config:

- `##` and `###` only — never `#`; the layout owns the single `h1`
- Callouts must be exactly `> [!NOTE]`, `[!TIP]`, `[!WARNING]`, `[!IMPORTANT]` or `[!CAUTION]`
- Always tag a code fence with its language
- Mermaid is the diagram language; no image files are committed
- End with a `## References` section

### Validate before you commit

```bash
python scripts/blog/validate_style.py _posts/2026-08-10-your-post.md
python scripts/blog/quality.py _posts/2026-08-10-your-post.md
```

`validate_style.py` checks structure: front matter key order, required fields,
the category enum, heading depth, callout markers and the filename date.
`quality.py` scores editorial quality against the rubric and must clear
`rubric.gate` (80). Both run in CI on every PR that touches `_posts/`.

The cover image is **generated**, not authored. `_includes/cover-tile.html`
derives a deterministic 16:9 tile from the post slug and its primary category
accent, so every post gets one and no image files are ever committed. To
disable it, set `images.cover.enabled: false` in the config.

---

## Project Structure

```
.
├── _data/
│   └── blog_style.yml         # THE style config: tokens, covers, structure, rubric
├── _posts/                    # Your Markdown blog posts
├── _layouts/
│   ├── default.html           # Base HTML shell (head, tokens, header, footer, JS)
│   ├── post.html              # Article layout: progress bar, cover, left TOC, share
│   └── page.html              # Generic non-post page
├── _includes/
│   ├── tokens.html            # Emits blog_style.yml as :root CSS variables
│   ├── cover-tile.html        # Deterministic 16:9 cover (no image files)
│   ├── author-card.html       # Author bio card
│   ├── share.html             # Share buttons
│   ├── header.html            # Site navigation
│   ├── footer.html            # Footer: sitemap, RSS, socials
│   └── blog-card.html         # Post card for the listing
├── assets/
│   ├── css/main.css           # All styles (no build step); :root is a token fallback
│   └── js/main.js             # TOC, callouts, code boxes, progress bar, share
├── index.html                 # Blog listing page (/)
├── scripts/
│   └── blog/
│       ├── server.py          # Flask dev server
│       ├── liquid_render.py   # Liquid renderer for the dev server
│       ├── new_post.py        # Scaffolds a post from blog_style.yml
│       ├── validate_style.py  # Structural check (front matter, headings, callouts)
│       ├── quality.py         # Editorial score against the config rubric
│       ├── generate.py        # AI post generation
│       ├── research.py        # AI topic research
│       ├── github_api.py      # GitHub PR publishing
│       └── ai_provider.py     # OpenAI / Anthropic abstraction
├── _config.yml                # Site metadata and Jekyll config
├── .env.example               # Environment variable template
└── requirements.txt           # Python dependencies
```

---

## AI Post Generation (Optional)

The `scripts/blog/` tools let you draft and publish posts with AI assistance.

> Requires `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in your `.env`

**Research a topic:**
```bash
python scripts/blog/research.py "Kafka consumer group rebalancing"
```

**Generate a draft post:**
```bash
python scripts/blog/generate.py "How Go's sync.Map works"
```

**Check post quality:**
```bash
python scripts/blog/quality.py _posts/2026-08-10-my-post.md
```

**Publish via GitHub PR:**
```bash
python scripts/blog/github_api.py _posts/2026-08-10-my-post.md
```

---

## Customization

Almost everything visual is one file. Read
**[`_data/blog_style.yml`](_data/blog_style.yml)** first.

### Changing colors / fonts

Edit the `tokens:` block. `_includes/tokens.html` renders it as a `<style>` block
after `main.css`, so it wins, and the copy in `main.css` acts only as a fallback:

```yaml
tokens:
  color:
    bg: "#fafaf8"        # page background
    accent: "#2563eb"    # links, buttons, active states
    text: "#1a1916"      # body text
    code_bg: "#181825"   # code block surface
  font:
    sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
  space:
    lg: "1.5rem"
```

### Adding or renaming a category

`structure.category_enum` is the controlled vocabulary. It drives the listing
filter tabs, the per-category cover colour in `images.category_accent`, and both
checkers. Add the name to the enum *and* a matching accent:

```yaml
structure:
  category_enum: [AI, Backend, ..., MyNewTopic]
images:
  category_accent:
    default: "#2563eb"
    MyNewTopic: "#7c3aed"
```

### Toggling post furniture

`navigation:` turns the reading progress bar, share buttons, author card and
previous/next on and off without touching a layout:

```yaml
navigation:
  show_reading_progress: true
  show_share: true
  show_author_card: true
  show_prev_next: true
```

### Cover images

Covers are generated, never committed. `images.cover` controls the aspect ratio,
how many pattern variants exist, and whether the tile shows on the post page,
on cards, or both. Set `images.cover.enabled: false` to remove them entirely.

### The quality gate

`rubric:` in the config holds the score weights (which must total 100) and
`gate`, the score a post must reach in CI. Changing the gate is a one-line edit.

### Site metadata

Edit [`_config.yml`](_config.yml) for the site title, description, and URL:

```yaml
title: "Saiteja's Dev Blog"
url: "https://chadasaiteja.github.io"
```

---

## Continuous Integration

`.github/workflows/validate-blog.yml` runs on every PR that touches `_posts/`,
and on pushes to `main` that change the style config, layouts or includes. It:

1. Parses `_data/blog_style.yml` and asserts the rubric weights total 100
2. Asserts every layout and include still parses
3. Runs `validate_style.py` then `quality.py` on each changed post
4. Runs the unit tests
5. Builds the site with `jekyll-build-pages` as a smoke test

---

## Deploying to GitHub Pages

This repository is set up with a GitHub Actions workflow to automatically build and deploy the blog to GitHub Pages.

### Setup Instructions
1. Push this code to a GitHub repository named `blog` (e.g. `github.com/chadasaiteja/blog`).
2. Go to your repository settings: **Settings** → **Pages**.
3. Under **Build and deployment** → **Source**, select **GitHub Actions**.
4. Push a new post or update to the `master` or `main` branch.
5. The GitHub Action will trigger, build the Jekyll static site, and deploy it to `https://chadasaiteja.github.io/blog/`.

---

## License

MIT — feel free to use this as a template for your own blog.

