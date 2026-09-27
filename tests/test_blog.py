import unittest
import os
import sys
import tempfile
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "scripts", "blog"))

from quality import BlogQualityAnalyzer, load_config
from new_post import build_front_matter, build_body
from liquid_render import LiquidRenderer, render_layout, ALLOWED_FILTERS
from validate_style import validate
from server import parse_markdown_file, write_markdown_file

WORKSPACE = ROOT

CANONICAL_POST = """---
layout: post
title: "A Canonical Post For The Style Validator"
description: "A description written to sit inside the fifty to one hundred and sixty character bounds the style config declares."
date: 2026-01-01
categories:
  - Backend
tags:
  - example
author: "Saiteja Chada"
reading_time: "5 min read"
draft: false
---
An opening paragraph that comfortably clears the thirty word floor that the
structure rules apply before the first heading is allowed to appear.

## Background

Some context for the reader, long enough that the section is not flagged as
too short by the thirty word minimum in the style configuration file.

> [!NOTE]
> A callout using one of the configured markers.

## How It Works

```bash
# A shell comment, not a body heading
echo hello
```

## Key Takeaways

- One bullet.
- Another bullet.

## References

1. [Example](https://example.com/real)
"""

BROKEN_POST = """---
layout: post
title: "Broken"
description: "short"
date: 2026-01-02
draft: true
author: "x"
categories:
  - NotARealCategory
tags: []
mystery_key: true
---
Body text.

# An H1 in the body

> [!NONSENSE]
> Unrecognised marker.
"""

class TestBlogAutomation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        self.test_dir.cleanup()

    def test_slug_generation(self):
        title = "Understanding Kafka! Message (Ordering) & Execution"
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug).strip("-")
        self.assertEqual(slug, "understanding-kafka-message-ordering-execution")

    def test_frontmatter_read_write(self):
        temp_filepath = os.path.join(self.test_dir.name, "test-post.md")
        metadata = {
            "layout": "post",
            "title": "Unit Test Blog Post",
            "date": "2026-08-09",
            "categories": ["Testing", "Python"],
            "tags": ["unittest", "ci"],
            "author": "Saiteja",
            "draft": True
        }
        body = "This is the body of the unit test post. It contains some markdown text."
        
        write_markdown_file(temp_filepath, metadata, body)
        read_meta, read_body = parse_markdown_file(temp_filepath)
        
        self.assertEqual(read_meta["title"], metadata["title"])
        self.assertEqual(read_meta["date"], metadata["date"])
        self.assertEqual(read_meta["author"], metadata["author"])
        self.assertEqual(read_meta["draft"], metadata["draft"])
        self.assertEqual(read_meta["categories"], metadata["categories"])
        self.assertEqual(read_meta["tags"], metadata["tags"])
        self.assertEqual(read_body.strip(), body.strip())

    def test_quality_analyzer_scoring(self):
        temp_filepath = os.path.join(self.test_dir.name, "test-quality-post.md")
        
        weak_content = """---
layout: post
title: "Short"
description: ""
date: 2026-08-09
categories: []
tags: []
author: ""
draft: true
---
Too short body content.
"""
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(weak_content)
            
        analyzer = BlogQualityAnalyzer(temp_filepath)
        analyzer.analyze()
        weak_score = analyzer.get_total_score()
        
        self.assertTrue(weak_score < 70)
        self.assertTrue(any("Missing description" in w or "SEO: Missing description" in w for w in analyzer.warnings))
        self.assertTrue(any("Add at least 1 category" in w or "Quality: Categories are missing" in w for w in analyzer.warnings))

        strong_content = """---
layout: post
title: "Implementing Resilient Redis Caching"
description: "A comprehensive guide on setting up Redis cache strategies, TTL rules, and key expulsion policies in Go."
date: 2026-08-09
categories:
  - Backend
  - DataStructures
tags:
  - redis
  - golang
  - databases
author: "Saiteja"
draft: false
---
Caching is an essential component of high-performance backend systems. It helps reduce database read loads and improves response times for frequently requested assets. In modern distributed systems, data stores like Redis and Memcached are frequently used to handle millions of queries per second. While Memcached is highly efficient for simple key-value structures, Redis offers rich data structures such as lists, sets, sorted sets, and hashes, making it much more versatile for complex caching patterns and transient state management.

In this guide, we will look at how to implement a cache-aside strategy in Go using Redis. Cache-aside is highly resilient because a caching layer failure does not crash the application; instead, the application falls back directly to querying the database, albeit with increased latency.

## The Cache Aside Pattern

The cache-aside pattern is the most common caching pattern:
- The application tries to read from the cache first.
- If it is a cache hit, return the data.
- If it is a cache miss, read from the database, write to the cache, and return the data.

This process ensures that data is only loaded into the cache when it is explicitly requested, which helps conserve caching memory resources. However, it can lead to a slight overhead on cache misses, as the application has to query both the cache and the primary database. Furthermore, we must establish dynamic cache invalidation rules so that updates to the database are either written to the cache immediately or the cache keys are evicted to prevent returning stale data to users.

## Implementation in Go

Here is how to set up the Redis client and implement cache-aside logic:

```go
package main

import (
	"context"
	"fmt"
	"time"
	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()

func main() {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	
	err := rdb.Set(ctx, "user:101", "{id: 101, name: 'Saiteja'}", 5*time.Minute).Err()
	if err != nil {
		panic(err)
	}
	
	fmt.Println("Cache set successfully!")
}
```

## Key Takeaways

When deploying a production cache, keep these critical architectural patterns in mind:

- **TTL Bounds:** Always set a Time-To-Live (TTL) on cached keys to prevent stale data. A good practice is to set a randomized jitter on TTLs (e.g. 5 minutes +/- 30 seconds) to prevent all keys from expiring at the exact same moment, which can cause a sudden traffic spike to your database.

- **Cache Stampede:** Use mutexes or singleflight in Go to prevent multiple concurrent goroutines from fetching database resources on cache misses. This ensures only one worker queries the database, while other requests block and wait for the result.

- **Write Invalidation:** Decide on a write policy. Under a Write-Through cache scheme, updates are written to the database and the cache simultaneously. Under a Write-Back cache, updates are written to the cache first and asynchronously flushed to the database. Choose the policy that matches your read-to-write ratio.

- **Connection Pools:** Ensure that your Go redis client connection pool size is configured appropriately to support high concurrency under peak traffic scenarios without leaking socket file descriptors.

## References
1. [Redis Official Documentation - Caching Guide](https://redis.io/docs/manual/client-side-caching/)
2. [Designing Data-Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) by Martin Kleppmann.
"""
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(strong_content)
            
        analyzer_strong = BlogQualityAnalyzer(temp_filepath)
        analyzer_strong.analyze()
        strong_score = analyzer_strong.get_total_score()
        
        print("WARNINGS GATHERED:", analyzer_strong.warnings)
        self.assertTrue(strong_score >= 90)
        self.assertEqual(len(analyzer_strong.warnings), 0)

    # ------------------------------------------------------------------
    # The style config is the single source of truth. These tests fail loudly
    # if the config, the scaffolding or the analyser drifts apart.
    # ------------------------------------------------------------------
    def test_style_config_weights_sum_to_one_hundred(self):
        config = load_config()
        self.assertEqual(sum(config["rubric"]["weights"].values()), 100)
        self.assertEqual(config["rubric"]["gate"], 80)
        for required_key in ("tokens", "structure", "rubric"):
            self.assertIn(
                required_key, config,
                "_data/blog_style.yml must define {}".format(required_key),
            )

    def test_templates_only_read_config_keys_that_exist(self):
        """Every site.data.blog_style path a template reads must resolve.

        A config key can be removed or commented out and every template will
        still render -- Liquid resolves a missing key to nil, prints nothing and
        raises nothing. That is how the author card came to render as an empty
        box and the footer as an empty brand, with no error anywhere. This test
        turns that class of mistake into a named failure.

        Aliases are resolved per file, because a template may assign any of:
            bs = site.data.blog_style          -> bs.tokens.color
            bs = site.data.blog_style.tokens   -> bs.color
        """
        config = load_config()

        # Roots that a template only reads behind an existence check, so their
        # absence is deliberate rather than a bug.
        optional_roots = {"author_profile"}

        assign_re = re.compile(
            r"\{%-?\s*assign\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
            r"site\.data\.blog_style((?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*-?%\}"
        )
        direct_re = re.compile(
            r"site\.data\.blog_style((?:\.[A-Za-z_][A-Za-z0-9_]*)+)"
        )

        templates = []
        for base in ("_layouts", "_includes"):
            for name in sorted(os.listdir(os.path.join(ROOT, base))):
                templates.append(os.path.join(base, name))
        templates.append("index.html")

        # Liquid exposes these on a list as properties, not as config keys.
        list_properties = {"size", "first", "last"}

        def first_missing(segments):
            value = config
            for segment in segments:
                if isinstance(value, (list, str)) and segment in list_properties:
                    continue
                if isinstance(value, dict) and segment in value:
                    value = value[segment]
                else:
                    return segment
            return None

        problems = []
        for relative in templates:
            path = os.path.join(ROOT, relative)
            if not path.endswith((".html", ".md")):
                continue
            with open(path, encoding="utf-8") as handle:
                source = handle.read()

            references = []

            for match in direct_re.finditer(source):
                segments = [s for s in match.group(1).split(".") if s]
                references.append(segments)

            # Local aliases, with the path they were assigned from.
            for match in assign_re.finditer(source):
                alias, prefix = match.group(1), match.group(2)
                prefix_segments = [s for s in prefix.split(".") if s]
                alias_re = re.compile(
                    r"\b" + re.escape(alias) + r"((?:\.[A-Za-z_][A-Za-z0-9_]*)+)"
                )
                for use in alias_re.finditer(source):
                    tail = [s for s in use.group(1).split(".") if s]
                    references.append(prefix_segments + tail)

            for segments in references:
                if not segments or segments[0] in optional_roots:
                    continue
                missing = first_missing(segments)
                if missing:
                    problems.append(
                        "{} reads site.data.blog_style.{} but _data/blog_style.yml "
                        "has no '{}'".format(relative, ".".join(segments), missing)
                    )

        self.assertEqual(problems, [], "\n".join(problems))

    def test_quality_scores_are_driven_by_the_config(self):
        config = load_config()
        analyzer = BlogQualityAnalyzer(os.path.join(self.test_dir.name, "missing.md"), config)
        self.assertEqual(analyzer.scores, config["rubric"]["weights"])

    def test_shell_comments_in_fences_are_not_headings(self):
        temp_filepath = os.path.join(self.test_dir.name, "fence-post.md")
        content = """---
layout: post
title: "Installing a Toolchain With Comments In Fences"
description: "A post whose bash and python fences contain hash-prefixed comment lines that must not be read as body H1 headings."
date: 2026-08-09
categories:
  - DevTools
tags:
  - bash
author: "Saiteja"
reading_time: "5 min read"
draft: false
---
""" + "\n".join([
            "This opening paragraph is deliberately long enough to clear the "
            "thirty word floor that the structure check applies before the "
            "first heading appears in the document.",
            "",
            "## Setup",
            "",
            "Run the installer and then install the dependencies it needs.",
            "",
            "```bash",
            "# Using apt to install the toolchain",
            "# Add the repository first, then update",
            "apt-get update && apt-get install -y build-essential",
            "```",
            "",
            "```python",
            "# Add elements to the collection",
            "for item in items:",
            "    total += item",
            "```",
            "",
            "### Verifying",
            "",
            "The installer prints a version banner once it finishes writing "
            "every file into the toolchain directory on this machine.",
            "",
            "```bash",
            "toolchain --version",
            "```",
            "",
            "## Key Takeaways",
            "",
            "- Comments inside a fenced block are not document headings.",
            "- The heading scan is fence aware so shell comments never cost points.",
            "- Real body headings still resolve to h2 and h3 as the config requires.",
            "",
            "## References",
            "",
            "1. [GNU Bash Manual](https://www.gnu.org/software/bash/manual/)",
            "2. [Python Tutorial](https://docs.python.org/3/tutorial/)",
        ]) + "\n"
        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(content)

        analyzer = BlogQualityAnalyzer(temp_filepath)
        analyzer.analyze()

        h1_warnings = [w for w in analyzer.warnings if "H1" in w]
        self.assertEqual(h1_warnings, [], "hash-prefixed lines inside fences must not be read as H1")
        self.assertEqual([h[1] for h in analyzer.headings if h[1] == 1], [])

    def test_new_post_scaffolds_from_the_config(self):
        config = load_config()
        order = config["structure"]["frontmatter_order"]

        front_matter = build_front_matter(
            {
                "layout": "post",
                "title": "A Config Driven Title",
                "description": "A description that satisfies the configured length bounds.",
                "date": "2026-08-09",
                "categories": ["Backend"],
                "tags": ["one", "two"],
                "draft": False,
            },
            config,
        )

        keys = [
            line.split(":")[0]
            for line in front_matter.splitlines()
            if line and not line.startswith("---") and not line.startswith("  - ")
        ]
        self.assertEqual(keys, [k for k in order if k in keys])
        self.assertIn("categories:", front_matter)
        self.assertIn("  - Backend", front_matter)
        self.assertIn("draft: false", front_matter)

    def test_new_post_body_uses_the_configured_sections(self):
        config = load_config()
        body = build_body(config)
        configured = [
            s["heading"] for s in config["structure"]["sections"] if s.get("heading")
        ]
        for heading in configured:
            self.assertIn("## {}".format(heading), body)
        self.assertIn("## References", body)
        # The layout owns the single h1, so the body must never emit one.
        self.assertNotIn("\n# ", body)

    # ------------------------------------------------------------------
    # The dev server renders the real layouts, so the Liquid subset has to
    # handle every construct _layouts/ and _includes/ actually use.
    # ------------------------------------------------------------------
    def setUpRenderer(self):
        return LiquidRenderer(WORKSPACE)

    def test_liquid_filters_and_whitespace_control(self):
        r = self.setUpRenderer()
        out = r.render(
            '{%- assign a = "ab" | split: "" -%}'
            "{%- for c in a -%}[{{ c }}]{%- endfor -%}"
            '{{ "Hi_There" | replace: "_", "-" | upcase }}',
            [{"site": {"baseurl": "/blog"}}],
        )
        self.assertEqual(out, "[a][b]HI-THERE")

    def test_liquid_hash_iteration_yields_pairs(self):
        r = self.setUpRenderer()
        out = r.render(
            "{%- assign h = site.data -%}{%- for pair in h -%}"
            "{{ pair[0] }}={{ pair[1] }}{%- unless forloop.last -%},{%- endunless -%}"
            "{%- endfor -%}",
            [{"site": {"data": {"a": "1", "b": "2"}}}],
        )
        self.assertEqual(out, "a=1,b=2")

    def test_liquid_assign_survives_a_loop(self):
        # index.html builds its used-category set this way. `assign` inside a
        # `{% for %}` must write to the outermost scope, and the delimited
        # string plus `contains` is how the dedup is done without a `push`
        # filter, which Liquid does not have.
        r = self.setUpRenderer()
        out = r.render(
            '{%- assign used = "|" -%}'
            "{%- for post in site.posts -%}"
            "{%- for cat in post.categories -%}"
            '{%- assign token = "|" | append: cat | append: "|" -%}'
            "{%- unless used contains token -%}"
            '{%- assign used = used | append: cat | append: "|" -%}'
            "{%- endunless -%}"
            "{%- endfor -%}{%- endfor -%}"
            "{{ used }}",
            [{"site": {"posts": [
                {"categories": ["AI", "Backend"]},
                {"categories": ["AI", "Security"]},
            ]}}],
        )
        self.assertEqual(out, "|AI|Backend|Security|")

    def test_liquid_contains_guard_rejects_substrings(self):
        # Without the pipe delimiters, the category "Go" would match inside a
        # longer name and create a filter tab that leads nowhere.
        r = self.setUpRenderer()
        self.assertEqual(
            r.render('{%- assign used = "|GoLevel|" -%}'
                     '{%- assign token = "|" | append: "Go" | append: "|" -%}'
                     "{% if used contains token %}MATCHED{% else %}SAFE{% endif %}", [{}]),
            "SAFE",
        )
        self.assertEqual(
            r.render('{%- assign used = "|Go|" -%}'
                     '{%- assign token = "|" | append: "Go" | append: "|" -%}'
                     "{% if used contains token %}MATCHED{% else %}SAFE{% endif %}", [{}]),
            "MATCHED",
        )

    def test_liquid_include_receives_keyword_arguments(self):
        r = self.setUpRenderer()
        out = r.render(
            "{% include share.html %}",
            [{"site": {"data": {"blog_style": {"navigation": {"share_targets": ["copy"]}}}}}],
        )
        self.assertIn('class="share"', out)
        self.assertIn('data-share-target="copy"', out)
        self.assertNotIn('data-share-target="x"', out)

    def test_liquid_case_when_selects_one_branch(self):
        r = self.setUpRenderer()
        template = "{%- case t -%}{%- when 'a' -%}A{%- when 'b' -%}B{%- else -%}OTHER{%- endcase -%}"
        for value, expected in (("a", "A"), ("b", "B"), ("z", "OTHER")):
            self.assertEqual(r.render(template, [{"t": value}]), expected)

    def test_liquid_where_exp_filters_a_collection(self):
        r = self.setUpRenderer()
        out = r.render(
            '{%- assign live = site.posts | where_exp: "p", "p.draft != true" -%}'
            "{{ live.size }}",
            [{"site": {"posts": [{"draft": False}, {"draft": True}]}}],
        )
        self.assertEqual(out, "1")

    def test_liquid_reports_constructs_it_cannot_render(self):
        r = self.setUpRenderer()
        r.render("{% tablerow x in y %}{% endtablerow %}", [{"y": []}])
        self.assertTrue(r.unsupported, "an unknown tag must be reported, not dropped silently")

    def test_liquid_rejects_filters_liquid_does_not_have(self):
        # Liquid has no `push` and no `index` filter. Both got into the
        # templates once and failed silently on the real Jekyll build, so the
        # renderer refuses anything outside the known set.
        for name in ("push", "index"):
            r = self.setUpRenderer()
            r.render("{{ x | %s: 1 }}" % name, [{"x": [1, 2]}])
            self.assertTrue(
                r.unsupported,
                "the `{}` filter must be reported as unsupported".format(name),
            )

    def test_templates_only_use_filters_liquid_actually_has(self):
        """Scan every template for `| filter` and check the allowlist.

        This is the check that would have caught the production bug: a filter
        that renders fine under scripts/blog/liquid_render.py but does not exist
        in Shopify Liquid, so the GitHub Pages build fails or silently no-ops.
        """
        patterns = [
            os.path.join(ROOT, "_layouts", name) for name in os.listdir(os.path.join(ROOT, "_layouts"))
        ] + [
            os.path.join(ROOT, "_includes", name) for name in os.listdir(os.path.join(ROOT, "_includes"))
        ] + [os.path.join(ROOT, "index.html")]

        # `| limit: 2` is a for-loop argument, and a bare `|` inside prose is
        # just a character; only real filter positions are interesting.
        filter_re = re.compile(r"\|\s*([a-z_][a-z0-9_]*)\s*:")
        found = {}
        for path in patterns:
            if not path.endswith((".html", ".md")):
                continue
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            # Drop prose lines and HTML attributes before scanning.
            source = re.sub(r"<[^>]*>", " ", source)
            for name in filter_re.findall(source):
                found.setdefault(name, []).append(os.path.basename(path))

        # for-loop arguments that look like filters but are not
        loop_args = {"limit", "offset", "reversed", "cols"}

        offenders = {
            name: files for name, files in found.items()
            if name not in ALLOWED_FILTERS and name not in loop_args
        }
        self.assertEqual(
            offenders, {},
            "these filters are not in the standard Shopify Liquid set and would "
            "break the GitHub Pages build: {}".format(offenders),
        )

    def test_templates_do_not_use_where_exp(self):
        # where_exp is Jekyll-only. It works on GitHub Pages but not in a plain
        # Liquid engine, which is what makes the templates hard to verify.
        # Draft filtering uses `unless` instead.
        for base in ("_layouts", "_includes"):
            directory = os.path.join(ROOT, base)
            for name in os.listdir(directory):
                path = os.path.join(directory, name)
                with open(path, encoding="utf-8") as handle:
                    self.assertNotIn(
                        "where_exp", handle.read(),
                        "{} must not use the Jekyll-only where_exp filter".format(path),
                    )

    def test_every_layout_and_include_renders_without_leftover_liquid(self):
        config = load_config()
        site = {
            "title": "t", "description": "d", "url": "https://example.com",
            "baseurl": "/blog", "time": datetime(2026, 1, 1),
            "data": {"blog_style": config},
            "posts": [{
                "title": "A Post", "description": "A description long enough to pass the bounds.",
                "url": "/blog/a-post", "slug": "a-post", "date": "2026-01-01",
                "categories": ["Backend"], "tags": ["one"], "draft": False,
            }],
        }
        page = dict(site["posts"][0])
        page.update({"layout": "post", "author": "Saiteja Chada", "reading_time": "5 min read",
                     "previous": None, "next": None})

        post_html, unsupported_post = render_layout(WORKSPACE, "post", {"site": site, "page": page}, "<p>Body</p>")
        final_html, unsupported_default = render_layout(
            WORKSPACE, "default", {"site": site, "page": page}, post_html
        )

        self.assertEqual(unsupported_post, [], "post.html uses something the renderer cannot do")
        self.assertEqual(unsupported_default, [], "default.html uses something the renderer cannot do")
        self.assertNotRegex(final_html, r"\{%|\{\{")

        for expected in ('id="reading-progress-bar"', 'id="toc-list"',
                         'class="toc-mobile"', 'data-share', "--accent:",
                         "--header-height:"):
            self.assertIn(expected, final_html, "post page is missing {}".format(expected))

        # Covers are switched off in the config for now, so the tile must be
        # absent. Flipping images.cover.enabled back to true must bring it back.
        covers_enabled = config["images"]["cover"]["enabled"]
        if covers_enabled:
            self.assertIn('class="cover-tile', final_html)
        else:
            self.assertNotIn('class="cover-tile', final_html)
            self.assertNotIn("post-hero", final_html)

        # The author card needs both navigation.show_author_card and a populated
        # author_profile. Either one off means the card must not render at all,
        # never render empty.
        card_wanted = config["navigation"].get("show_author_card", False)
        card_possible = card_wanted and bool(config.get("author_profile"))
        if card_possible:
            self.assertIn('class="author-card"', final_html)
        else:
            self.assertNotIn('class="author-card"', final_html)

    # ------------------------------------------------------------------
    # validate_style.py
    # ------------------------------------------------------------------
    def write_post(self, filename, body):
        path = os.path.join(self.test_dir.name, filename)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        return path

    def test_validate_style_accepts_a_canonical_post(self):
        path = self.write_post("2026-01-01-canonical.md", CANONICAL_POST)
        errors, warnings = validate(path, load_config())
        self.assertEqual(errors, [])
        self.assertEqual([w for w in warnings if "h4" in w or "h5" in w], [])

    def test_validate_style_flags_structural_problems(self):
        path = self.write_post("2026-01-02-broken.md", BROKEN_POST)
        errors, _ = validate(path, load_config())
        joined = " | ".join(errors)
        self.assertIn("h1 in the body", joined)
        self.assertIn("category not in structure.category_enum", joined)
        self.assertIn("unknown callout marker", joined)
        self.assertIn("out of order", joined)
        self.assertIn("unknown front matter key", joined)

if __name__ == "__main__":
    unittest.main()
