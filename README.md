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

---

## Writing a Post

Posts live in `_posts/` and follow Jekyll naming: `YYYY-MM-DD-slug.md`

### Frontmatter

Every post needs this block at the top:

```yaml
---
layout: post
title: "Your Post Title"
description: "A one-line summary shown in cards and meta tags."
date: 2026-08-10
categories:
  - Go
  - Backend
tags:
  - golang
  - concurrency
author: "Saiteja"
reading_time: "5 min read"
draft: false
---
```

| Field | Required | Notes |
|---|---|---|
| `title` | ✅ | Shown in cards, page title, and `<h1>` |
| `description` | ✅ | Card excerpt + meta description |
| `date` | ✅ | `YYYY-MM-DD` format |
| `categories` | ✅ | Used for filter tabs on `/blog/` |
| `tags` | optional | Shown as `#tag` badges |
| `author` | optional | Shown in post meta row |
| `reading_time` | optional | Defaults to `"5 min read"` |
| `draft` | optional | Set `true` to hide from listing |

### Then write your content in Markdown

```markdown
## The Problem

Paragraph text here...

### Sub-heading

- Bullet one
- Bullet two

\```typescript
const example = "code blocks work too";
\```
```

---

## Project Structure

```
.
├── _posts/                  # Your Markdown blog posts
├── _layouts/
│   ├── default.html         # Base HTML shell (head, header, footer)
│   └── post.html            # Article page layout with TOC
├── _includes/
│   ├── header.html          # Site navigation
│   ├── footer.html          # Footer
│   └── blog-card.html       # Post card component
├── assets/
│   └── css/
│       └── main.css         # All styles (single file, no build step)
├── blog/
│   └── index.html           # Blog listing page (/blog/)
├── index.html               # Homepage (/)
├── scripts/
│   └── blog/
│       ├── server.py        # Flask dev server + rendering engine
│       ├── generate.py      # AI post generation
│       ├── research.py      # AI topic research
│       ├── quality.py       # Post quality analysis
│       ├── github_api.py    # GitHub PR publishing
│       └── ai_provider.py   # OpenAI / Anthropic abstraction
├── _config.yml              # Site metadata and Jekyll config
├── .env.example             # Environment variable template
└── requirements.txt         # Python dependencies
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

### Changing colors / fonts

All design tokens are CSS variables at the top of [`assets/css/main.css`](assets/css/main.css):

```css
:root {
  --bg:      #fafaf8;   /* page background */
  --accent:  #2563eb;   /* links, buttons, active states */
  --text:    #1a1916;   /* body text */
  /* ... */
}
```

### Adding filter tabs on `/blog/`

Edit the filter buttons in [`blog/index.html`](blog/index.html):

```html
<button class="filter-tab" data-filter="go">Go</button>
```

The filter matches against post titles, descriptions, categories, and tags — so just make sure your posts have matching `categories` or `tags`.

### Site metadata

Edit [`_config.yml`](_config.yml) for the site title, description, and URL:

```yaml
title: "Saiteja's Dev Blog"
url: "https://chadasaiteja.github.io"
```

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

