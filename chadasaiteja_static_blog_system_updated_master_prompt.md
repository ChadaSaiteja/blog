# Master Build Prompt — Personal Static Developer Blog System

## 1. Project Goal

Build a personal software-development blog system for:

`https://chadasaiteja.github.io`

Public blog URLs must follow:

`https://chadasaiteja.github.io/blog/<topic-name>`

Examples:

- `https://chadasaiteja.github.io/blog/kafka-ordering`
- `https://chadasaiteja.github.io/blog/go-concurrency`
- `https://chadasaiteja.github.io/blog/mongodb-indexing`

The public website must be a **static, content-first developer blog**, inspired by the simplicity and architecture of repositories such as `SriSatyaLokesh/learn-ai`.

The blog should have:

- A clean and simple UI
- Consistent reusable blog templates
- Markdown-based content
- Technical code examples
- Images/diagrams when they genuinely improve understanding
- References to trustworthy sources
- Good typography and readability
- Responsive/mobile support
- Search
- Categories/tags
- Previous/next navigation
- SEO metadata

The publishing workflow must be Git-native:

```text
Create content
    ↓
Research / optional AI assistance
    ↓
Generate structured Markdown
    ↓
Quality check
    ↓
Preview
    ↓
Create Git branch
    ↓
Commit blog
    ↓
Create Pull Request
    ↓
I review
    ↓
Merge to main
    ↓
GitHub Actions
    ↓
Jekyll build
    ↓
GitHub Pages
```

Do **not** automatically merge PRs in the MVP.

---

# 2. Important Architectural Principle

The blog content and the blog presentation must be separate.

The content-generation system must generate **Markdown + frontmatter**, not HTML.

Use:

```text
AI / Blog Creator
        ↓
Markdown
        ↓
Jekyll
        ↓
Liquid template
        ↓
HTML
        ↓
GitHub Pages
```

This allows the entire visual design to change later without rewriting existing blog content.

Do not generate individual HTML pages for every article.

---

# 3. Technology Stack

Use this stack unless there is a strong technical reason to change it.

## Public blog

- Jekyll 4.x
- Ruby
- Liquid templates
- Markdown
- Kramdown
- SCSS/CSS
- JavaScript where required

## Search

Use Lunr.js or another lightweight client-side static search implementation.

The search must work without a database/backend.

## Blog automation

Use Python for the content-generation/research/quality tooling unless a TypeScript/Node.js implementation is clearly simpler.

Python should handle:

- Blog generation orchestration
- Research integration
- AI provider abstraction
- Blog quality analysis
- Markdown/frontmatter generation
- GitHub API integration if appropriate

## AI

Implement an AI provider abstraction.

Do not hard-code the application to one AI vendor.

The system should be able to support a provider such as:

- Anthropic Claude
- OpenAI
- Another compatible provider later

API keys must never be exposed to browser/client-side code.

## GitHub

- GitHub repository
- GitHub API
- GitHub App or another secure server-side authentication mechanism
- Pull Requests
- GitHub Actions

## Hosting

GitHub Pages.

## Database

Do **not** use a database in the MVP.

The Git repository is the source of truth.

Do not introduce:

- PostgreSQL
- MongoDB
- Redis
- Firebase
- Supabase

unless a future requirement genuinely needs them.

---

# 4. Repository Structure

Create a clean repository similar to:

```text
chadasaiteja.github.io/
│
├── _posts/
│   ├── 2026-08-09-kafka-ordering.md
│   ├── 2026-08-15-go-concurrency.md
│   └── 2026-08-20-mongodb-indexing.md
│
├── _layouts/
│   ├── default.html
│   ├── post.html
│   └── page.html
│
├── _includes/
│   ├── header.html
│   ├── footer.html
│   ├── blog-card.html
│   ├── table-of-contents.html
│   ├── blog-navigation.html
│   └── share.html
│
├── _data/
│   ├── categories.yml
│   └── authors.yml
│
├── _sass/
│   ├── base.scss
│   ├── blog.scss
│   ├── layout.scss
│   └── syntax.scss
│
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
│
├── category/
│
├── tags/
│
├── scripts/
│   ├── blog/
│   │   ├── generate.py
│   │   ├── research.py
│   │   ├── quality.py
│   │   ├── markdown.py
│   │   └── github.py
│   │
│   └── ...
│
├── admin/
│   └── ...
│
├── .github/
│   └── workflows/
│       ├── deploy.yml
│       └── validate-blog.yml
│
├── _config.yml
├── Gemfile
├── package.json
├── README.md
└── .env.example
```

Adjust the structure if required, but preserve the separation between:

- Blog content
- Jekyll templates
- Styles
- Assets
- Blog automation
- GitHub integration
- CI/CD

---

# 5. Public Website

## Home page

Create a simple developer-focused homepage.

Include:

- Name
- Short developer introduction
- Latest/featured blogs
- Categories
- Link to all blogs
- Minimal navigation

Do not create a complicated landing page.

## Blog listing

URL:

`/blog`

Display:

- Title
- Description
- Published date
- Tags/categories
- Reading time
- Optional thumbnail/hero image

Provide search.

## Individual blog

URL:

`/blog/<slug>`

Example:

`/blog/kafka-ordering`

Every blog must use the same Jekyll `post` layout.

The page should support:

- Title
- Description
- Date
- Updated date
- Author
- Tags/categories
- Reading time
- Optional hero image
- Table of contents
- Article content
- Code blocks
- Syntax highlighting
- Copy-code button if practical
- Images
- Image captions
- Image attribution/source when required
- References
- Previous/next navigation
- Back to blog
- Footer

---

# 6. Blog Content Structure

Do not force every blog into exactly the same textual sections.

The **visual template must be consistent**, but the article structure should be flexible.

A good default structure is:

```text
Title

Short introduction

Why this matters

Problem

Concept

How it works

Implementation / Code

Example

Common mistakes

Production considerations

Key takeaways

References
```

Sections may be omitted or renamed when they do not naturally fit the topic.

For example:

## Tutorial

```text
Introduction
Problem
Concept
How it works
Implementation
Example
Common mistakes
Key takeaways
References
```

## Architecture article

```text
Introduction
Problem
Architecture
Design decisions
Tradeoffs
Implementation
Production considerations
Key takeaways
References
```

## Engineering experience/article

```text
Context
What happened
Root cause
What we changed
What we learned
Production considerations
Key takeaways
References
```

## Opinion/article

```text
Opening
Argument
Examples
Counterpoints
Practical implications
Conclusion
References
```

The AI/content generator should select an appropriate structure rather than blindly filling every section.

---

# 7. Blog Frontmatter

Every Markdown post should have validated frontmatter.

Example:

```yaml
---
layout: post
title: "Understanding Kafka Message Ordering"
description: "A practical explanation of Kafka ordering guarantees and how to prevent event status regression."
date: 2026-08-09
updated: 2026-08-09
categories:
  - Kafka
  - Backend
tags:
  - kafka
  - microservices
  - event-driven
author: "Saiteja"
draft: false
hero_image:
  src: ""
  alt: ""
  source: ""
  license: ""
---
```

Required:

- `layout`
- `title`
- `description`
- `date`
- `categories`
- `tags`
- `author`
- `draft`

Validate:

- Unique slug
- Valid date
- Required metadata
- Valid categories
- Valid tags
- Image metadata when images are used

The URL slug should be generated safely from the topic/title.

Do not allow arbitrary filesystem paths.

---

# 8. Blog Writing Input

The user should not have to understand Jekyll or HTML.

The primary input should be normal sentences, paragraphs, notes, and technical information.

Example:

```text
Topic:
Kafka message ordering

What I want to explain:

We had an issue where ReadyForInstall and
Pre-fieldCompleted events were not always
processed in the expected order.

ReadyForInstall could reach the middleware
before Pre-fieldCompleted.

The Salesforce status should not move backwards.

We need to maintain an ordered list of statuses
and only update Salesforce if the incoming event
represents a later state.

Kafka only guarantees ordering within a partition.
Using orderId as the Kafka key helps route related
events to the same partition.

We also need to consider retries, consumers,
idempotency, and multiple producers.

Include a practical example and TypeScript code.
```

The system should convert this into a polished technical article.

---

# 9. Blog Creator

Build a simple private/admin content creation workflow.

The admin interface is only for one user.

Do NOT build:

- Public registration
- User management
- Teams
- Organizations
- Role management
- Multi-tenant features

The creator should support:

- Topic
- Working title
- Raw notes
- Technical details
- Examples
- Code
- Key points
- Tags
- Categories
- References
- Optional image/diagram requirements

Preferred flow:

```text
Create Blog
     ↓
Enter topic + notes
     ↓
Research
     ↓
Generate outline
     ↓
Generate article
     ↓
Quality check
     ↓
Edit
     ↓
Preview
     ↓
Create PR
```

---

# 10. Research System

Research should be a separate logical step from writing.

Do not simply prompt the AI:

"Write a blog about Kafka."

Instead:

```text
User input
    ↓
Research
    ↓
Verified facts + sources
    ↓
User experience/context
    ↓
Outline
    ↓
Article
```

For technical topics, prefer:

1. Official documentation
2. Original project documentation
3. Standards/specifications
4. Reputable technical sources
5. Community sources when useful

Research results should preserve:

- Source title
- Source URL
- Important fact
- Optional publication/update date
- Why the source was used

Do not copy large amounts of source text.

Summarize and synthesize.

---

# 11. Images and Diagrams

Images are optional.

Do not add decorative images just because an article supports images.

Determine whether a visual actually helps.

Possible visual types:

### Concept article

```text
Explanation
    ↓
Diagram
    ↓
Explanation
```

### Coding article

```text
Explanation
    ↓
Code
    ↓
Output
    ↓
Explanation
```

### Architecture article

```text
Problem
    ↓
Architecture diagram
    ↓
Component explanation
    ↓
Tradeoffs
```

### Experience/article

```text
Problem
    ↓
Timeline/flow diagram
    ↓
Solution
    ↓
Lessons
```

When using external images:

- Prefer official assets
- Prefer public-domain images
- Prefer permissively licensed images
- Prefer sources with clear licensing
- Store source URL
- Store attribution/license metadata when required
- Do not copy copyrighted images without permission
- Avoid unnecessary hotlinking

For technical explanations, generated diagrams or simple SVG diagrams are often preferable to stock photos.

---

# 12. AI Provider Architecture

Create an abstraction such as:

```python
class AIProvider:
    def generate(self, prompt, context):
        pass
```

Possible implementations:

```text
AIProvider
├── OpenAIProvider
├── AnthropicProvider
└── FutureProvider
```

The application should not depend directly on one provider throughout the codebase.

Use environment variables for:

- Provider
- API key
- Model
- Optional configuration

Never put AI API keys in browser JavaScript.

---

# 13. Content Generation Pipeline

Implement a pipeline similar to:

```text
                    User Input
                        │
                        ▼
                 Research Agent
                        │
                        ▼
                  Outline Agent
                        │
                        ▼
                  Writer Agent
                        │
                        ▼
               Technical Reviewer
                        │
                        ▼
                Formatter Agent
                        │
                        ▼
                  Markdown File
```

The agents do not have to be separate processes.

They can be Python modules/classes.

Use a shared context object:

```python
class BlogContext:
    topic: str
    raw_notes: str
    research: list
    outline: dict
    draft: str
    review: dict
    metadata: dict
```

Keep each stage independently testable.

---

# 14. Blog Quality Checker

Build a quality checker inspired by the `learn-ai` repository's blog analyzer.

Use a 100-point scoring model.

Example:

```text
Content quality        30
Technical accuracy     20
Structure              15
Examples               10
Readability            10
References             10
SEO                     5
--------------------------
Total                  100
```

The exact scoring can evolve.

The checker should identify:

- Missing introduction
- Weak title
- Missing description
- Poor heading structure
- Very short sections
- Unsupported technical claims
- Missing examples where examples are useful
- Missing code where code is expected
- Missing references
- Broken links
- Missing image alt text
- Duplicate headings
- Excessively long paragraphs
- Excessive passive/unclear writing where detectable
- SEO metadata problems

Output example:

```text
BLOG QUALITY
────────────────────────

Content quality        28/30
Technical accuracy     19/20
Structure              14/15
Examples               10/10
Readability             9/10
References              10/10
SEO                      4/5

TOTAL                  94/100

Warnings:
- Add an example explaining multiple partitions.
- Explain retry behavior.
- Add a reference for the ordering guarantee.
```

Set a configurable minimum score for PR creation, for example:

`80/100`

Do not make the threshold impossible to change.

---

# 15. Preview

Before creating a PR, render the generated Markdown using the same Jekyll templates used by the production site.

The preview should show:

- Actual title
- Metadata
- Table of contents
- Headings
- Code
- Images
- References
- Navigation

The user should be able to:

```text
Edit
Preview
Create PR
```

Do not make the user discover layout problems after merging.

---

# 16. GitHub Publishing Automation

After preview and approval, the system should:

1. Generate the final Markdown file.
2. Validate metadata.
3. Validate slug.
4. Run the quality checker.
5. Create a new branch.

Example:

```text
blog/add-kafka-ordering
```

6. Add the Markdown post.

Example:

```text
_posts/2026-08-09-kafka-ordering.md
```

7. Add permitted images/assets if required.
8. Commit changes.

Example commit:

```text
Add blog: Understanding Kafka Message Ordering
```

9. Create a Pull Request against `main`.

Example:

```text
Add blog: Understanding Kafka Message Ordering
```

PR body should include:

```text
## Blog

Title: Understanding Kafka Message Ordering

Slug: kafka-ordering

Quality score: 94/100

## Summary

Short summary.

## Validation

- [x] Markdown generated
- [x] Frontmatter validated
- [x] Links checked
- [x] Quality score passed
- [x] Build passed
```

Return the PR URL to the admin UI.

Do not merge automatically.

---

# 17. GitHub Authentication

Never expose a GitHub Personal Access Token in the client.

Preferred solution:

- GitHub App
- Minimal repository permissions
- Server-side API calls

If a simpler secure approach is selected for a personal MVP, document the security tradeoff.

Required permissions should be minimal.

The system should never request unnecessary repository permissions.

---

# 18. GitHub Actions

Create workflows for:

## Validation

On Pull Requests:

```text
PR
 ↓
Install dependencies
 ↓
Validate Markdown
 ↓
Validate frontmatter
 ↓
Run quality checks
 ↓
Run Jekyll build
 ↓
Fail or pass
```

## Deployment

After merge to `main`:

```text
main
 ↓
GitHub Actions
 ↓
Install Ruby dependencies
 ↓
Build Jekyll
 ↓
Deploy GitHub Pages
```

Use GitHub's supported Pages deployment approach.

The site must correctly work under:

`https://chadasaiteja.github.io`

and:

`https://chadasaiteja.github.io/blog/<slug>`

---

# 19. Search

Implement lightweight static search.

Preferred:

```text
Jekyll
 ↓
Generate search index
 ↓
Lunr.js
 ↓
Browser search
```

Search should support:

- Blog title
- Description
- Tags
- Categories
- Content

Do not introduce a server-side search database.

---

# 20. Categories and Tags

Support categories and tags.

Example:

```yaml
categories:
  - Backend
  - Distributed Systems

tags:
  - Kafka
  - Event Driven
  - Microservices
```

Provide:

```text
/blog
/category/backend
/tags/kafka
```

or an equivalent clean URL structure.

Keep the implementation simple.

---

# 21. Reading Time

Calculate estimated reading time automatically from article content.

Display:

```text
8 min read
```

Do not require the author to manually enter it.

---

# 22. SEO

Implement:

- Page title
- Meta description
- Canonical URL
- Open Graph metadata
- Twitter/X card metadata where appropriate
- Sitemap
- RSS if practical
- Semantic HTML
- Correct heading hierarchy
- Image alt text
- Clean URLs

---

# 23. Accessibility

Ensure:

- Keyboard navigation
- Proper semantic HTML
- Visible focus states
- Good contrast
- Alt text
- Accessible code blocks
- Responsive layout
- Proper heading hierarchy
- Screen-reader-friendly navigation

---

# 24. UI Design

The public website should be inspired by clean technical blogs such as the style of minimalist developer blogs.

Do not copy another site's design directly.

Design principles:

- Minimal
- Technical
- Content-first
- Excellent typography
- Comfortable reading width
- Strong code readability
- Simple navigation
- Responsive
- Little/no unnecessary animation

Example:

```text
← All Blogs

Understanding Kafka Message Ordering

Backend · Kafka · Microservices
August 9, 2026 · 8 min read

────────────────────────────────

Introduction

...

## The Problem

...

## What Kafka Actually Guarantees

...

## Our Production Scenario

...

[diagram]

## Implementation

```typescript
...
```

## Key Takeaways

...

## References

...

────────────────────────────────

← Previous       All Blogs       Next →
```

---

# 25. Admin UI

The admin interface is private and only for one user.

It should provide:

```text
My Blog Publisher

Blogs
────────────────────────────
Kafka Ordering       Published
Go Concurrency       Draft
MongoDB Indexing     Published

[ + Create New Blog ]
```

Create page:

```text
Create New Blog

Topic
[........................]

Working Title
[........................]

What do you want to explain?
[........................
 ........................]

Technical details
[........................
 ........................]

Examples / code
[........................
 ........................]

Important points
[........................]

Tags
[........................]

References
[........................]

[ Research & Generate ]
```

After generation:

```text
Draft generated

[Edit Draft]
[Preview]
[Quality Check]
[Create PR]
```

Keep the admin interface simple.

---

# 26. Security

Requirements:

- No secrets in Git
- `.env.example`
- Server-side API keys
- Secure GitHub authentication
- Input validation
- Markdown sanitization where needed
- XSS protection
- Safe slug generation
- Safe file paths
- No arbitrary file writes
- No arbitrary GitHub repository operations
- Minimal GitHub permissions

---

# 27. Error Handling

Provide useful errors for:

- Invalid topic
- Duplicate slug
- Missing title
- Missing description
- Invalid frontmatter
- Research failure
- AI provider failure
- GitHub authentication failure
- Branch creation failure
- Commit failure
- PR creation failure
- Jekyll build failure
- Broken links
- Invalid images

Never silently fail.

---

# 28. Development Phases

Build this incrementally.

## Phase 1 — Static Blog Foundation

Build:

- Jekyll project
- GitHub Pages configuration
- `_posts`
- `_layouts`
- `_includes`
- `_sass`
- Home page
- Blog listing
- Individual blog pages
- Sample posts
- Responsive design

At the end:

```text
/blog
/blog/kafka-ordering
```

must work.

## Phase 2 — Blog Template

Implement:

- Metadata
- TOC
- Syntax highlighting
- Code copy
- Tags
- Categories
- Reading time
- References
- Previous/next
- Images
- SEO

## Phase 3 — Search

Implement static Lunr.js search.

## Phase 4 — Quality Analyzer

Build the Python blog quality checker.

## Phase 5 — Blog Creator

Build the private creator UI/workflow.

Support:

- Raw notes
- Structured metadata
- Draft generation
- Markdown editing
- Preview

## Phase 6 — Research + AI

Add:

- Research provider
- AI provider abstraction
- Outline generation
- Article generation
- Technical review
- References

Make these configurable.

## Phase 7 — GitHub Automation

Implement:

```text
Branch
Commit
PR
```

securely.

## Phase 8 — CI/CD

Implement:

```text
PR validation
Merge
Jekyll build
GitHub Pages deployment
```

## Phase 9 — Polish

Add:

- SEO
- Accessibility
- Error handling
- Documentation
- Tests
- Performance optimization

---

# 29. Testing

Add meaningful tests for:

- Slug generation
- Frontmatter validation
- Blog quality scoring
- Markdown generation
- Research result handling
- GitHub branch naming
- PR metadata
- Jekyll build
- Broken links where practical

At minimum, the CI pipeline must verify that the site builds successfully.

---

# 30. Local Development

The README must explain:

## Install Ruby dependencies

```bash
bundle install
```

## Install JavaScript dependencies

```bash
npm install
```

## Run Jekyll locally

Use the appropriate Jekyll command for the project.

Example:

```bash
bundle exec jekyll serve
```

Then access the local site.

## Run blog tooling

Document commands such as:

```bash
python scripts/blog/quality.py <post>
python scripts/blog/generate.py
```

Use the final implementation's actual commands rather than blindly copying these examples.

---

# 31. Environment Configuration

Provide:

```text
.env.example
```

Document variables such as:

```text
AI_PROVIDER=
AI_API_KEY=
AI_MODEL=

GITHUB_APP_ID=
GITHUB_PRIVATE_KEY=
GITHUB_INSTALLATION_ID=
GITHUB_OWNER=chadasaiteja
GITHUB_REPOSITORY=
```

Only include variables that the final implementation actually uses.

Never commit real credentials.

---

# 32. Definition of Done

The project is complete when I can do this:

### Public side

1. Open:

`https://chadasaiteja.github.io`

2. Open:

`/blog`

3. Browse blogs.
4. Search blogs.
5. Open:

`/blog/<topic-name>`

6. Read a clean, responsive technical article.
7. View code examples.
8. View diagrams/images where appropriate.
9. Navigate between articles.

### Publishing side

1. Open the private blog creator.
2. Enter a topic.
3. Explain the idea using normal sentences and paragraphs.
4. Add technical details.
5. Add examples/code.
6. Request research.
7. Generate an article.
8. Edit the Markdown.
9. Preview it.
10. Run quality checks.
11. Fix warnings if required.
12. Click Create PR.
13. System creates a branch.
14. System commits the Markdown/assets.
15. System creates a GitHub PR.
16. System shows the PR URL.
17. I review the PR.
18. I merge it.
19. GitHub Actions validates/builds it.
20. GitHub Pages publishes it.

The final public URL must become:

`https://chadasaiteja.github.io/blog/<topic-name>`

---

# 33. Engineering Rules

- Build real working functionality.
- Do not create fake/mock GitHub integration for the final implementation.
- Do not leave core features as TODOs.
- Do not over-engineer the MVP.
- Do not introduce a database.
- Do not introduce a full SPA framework unless absolutely necessary.
- Keep the public blog static.
- Keep Markdown as the source of truth.
- Keep Jekyll responsible for presentation.
- Keep AI/research responsible for content assistance.
- Keep GitHub responsible for version control and publishing.
- Keep GitHub Actions responsible for CI/CD.
- Keep secrets server-side.
- Use reusable Jekyll layouts/includes.
- Use reusable Python modules for blog automation.
- Write maintainable code.
- Add documentation.
- Add tests for important logic.
- Use meaningful commit messages.
- Do not automatically merge PRs.

---

# 34. Final Output Required From the Coding Agent

After implementing the project, provide:

1. Final architecture
2. Final repository structure
3. Technology choices and why
4. Local setup instructions
5. GitHub Pages setup instructions
6. GitHub authentication setup
7. Environment variables
8. How to create a blog
9. How the research/AI pipeline works
10. How quality scoring works
11. How PR creation works
12. How deployment works
13. Testing instructions
14. Any remaining manual configuration
15. Any known limitations

Before declaring the project complete, actually run the important build/test commands and fix errors.

If the repository already contains useful code/configuration, inspect it first and preserve useful parts rather than blindly replacing everything.

The final implementation should be a **simple, Git-native, static developer blog system with an intelligent content creation and publishing workflow**, not a traditional CMS.
