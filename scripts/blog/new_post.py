#!/usr/bin/env python3
"""Scaffold a new post from the shared style config.

The shape of every post -- front matter key order, defaults, category enum,
section skeleton, heading and callout rules -- comes from
_data/blog_style.yml. Nothing about a post's structure is defined here.

    python scripts/blog/new_post.py "How Redis Streams Actually Work"
    python scripts/blog/new_post.py --title "..." --categories Backend,DistributedSystems
    python scripts/blog/new_post.py --title "..." --draft
    python scripts/blog/new_post.py --print     # write to stdout, touch nothing
"""

import argparse
import os
import re
import sys
from datetime import date

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Run: pip install -r requirements.txt")

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(WORKSPACE, "_data", "blog_style.yml")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit("Missing style config: {}".format(CONFIG_PATH))
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-").lower()


def validate_categories(categories, config):
    """Warn on anything outside structure.category_enum rather than rejecting,
    so an in-progress draft is never blocked by the enum."""
    allowed = config["structure"].get("category_enum") or []
    if not allowed:
        return categories
    unknown = [c for c in categories if c not in allowed]
    if unknown:
        print(
            "warning: category not in structure.category_enum: {}".format(
                ", ".join(unknown)
            ),
            file=sys.stderr,
        )
        print("         allowed: {}".format(", ".join(allowed)), file=sys.stderr)
    return categories


def build_front_matter(values, config):
    """Emit front matter with the key order declared in the config."""
    order = config["structure"]["frontmatter_order"]
    # These are safe plain scalars in YAML, and the existing posts leave them
    # unquoted. Everything else is quoted.
    plain = {"layout"}
    lines = ["---"]
    for key in order:
        if key not in values or values[key] is None:
            continue
        value = values[key]
        if isinstance(value, list):
            if not value:
                continue
            lines.append("{}:".format(key))
            lines.extend("  - {}".format(item) for item in value)
        elif isinstance(value, bool):
            lines.append("{}: {}".format(key, "true" if value else "false"))
        elif key in plain:
            lines.append("{}: {}".format(key, value))
        else:
            lines.append('{}: "{}"'.format(key, str(value).replace('"', '\\"')))
    lines.append("---")
    return "\n".join(lines)


def build_body(config):
    """Emit the section skeleton declared in structure.sections."""
    rules = config["structure"]["rules"]
    parts = []

    parts.append(
        "<!--\n"
        "  Structure, heading rules, callout syntax and the References requirement\n"
        "  all come from _data/blog_style.yml. Read it before editing this file.\n"
        "-->"
    )

    for section in config["structure"]["sections"]:
        heading = section.get("heading")
        hint = section.get("hint") or ""
        if heading is None:
            parts.append("<!-- {} -->".format(hint))
        else:
            parts.append("## {}\n\n<!-- {} -->".format(heading, hint))
        parts.append("")

    parts.append("<!--")
    parts.append("  Reminders from structure.rules:")
    parts.append("    - no H1 in the body, the layout owns the single h1")
    parts.append("    - headings run {} to {}".format(
        rules.get("min_heading_level", 2), rules.get("max_heading_level", 3)))
    parts.append("    - callouts: {}".format(rules.get("callout_syntax", "")))
    parts.append("    - end with a '{}' section".format(
        rules.get("required_trailing_section", "References")))
    parts.append("-->")
    return "\n".join(parts).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a Jekyll post from _data/blog_style.yml"
    )
    parser.add_argument("topic", nargs="?", help="topic, used for title and slug")
    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument(
        "--categories", help="comma separated, validated against category_enum"
    )
    parser.add_argument("--tags", help="comma separated")
    parser.add_argument("--author")
    parser.add_argument("--reading-time", dest="reading_time")
    parser.add_argument("--slug")
    parser.add_argument(
        "--draft", action="store_true", help="write draft: true into the front matter"
    )
    parser.add_argument(
        "--print", dest="to_stdout", action="store_true",
        help="write the post to stdout instead of _posts/"
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = parser.parse_args()

    config = load_config()
    structure = config["structure"]
    defaults = structure["defaults"]

    title = args.title or args.topic
    if not title:
        parser.error("provide a topic or --title")

    slug = args.slug or slugify(title)
    if not slug:
        slug = "untitled-post"

    if args.categories:
        categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    else:
        categories = [defaults.get("categories", ["Backend"])]
    validate_categories(categories, config)

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    today = date.today().isoformat()

    values = {
        "layout": defaults.get("layout", "post"),
        "title": title,
        "description": args.description
        or "TODO: one sentence, {}-{} characters.".format(
            structure["rules"].get("min_description_chars", 50),
            structure["rules"].get("max_description_chars", 160),
        ),
        "date": today,
        "updated": today,
        "categories": categories,
        "tags": tags,
        "author": args.author or defaults.get("author", "Saiteja Chada"),
        "reading_time": args.reading_time or defaults.get("reading_time", "5 min read"),
        "draft": True if args.draft else defaults.get("draft", False),
    }
    values = {k: v for k, v in values.items() if v not in (None, [], "")}

    document = build_front_matter(values, config) + "\n\n" + build_body(config)

    if args.to_stdout:
        print(document)
        return

    filename = "{}-{}.md".format(today, slug)
    path = os.path.join(WORKSPACE, "_posts", filename)

    if os.path.exists(path) and not args.force:
        sys.exit("Refusing to overwrite {} (pass --force)".format(path))

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(document)

    print("Created {}".format(os.path.relpath(path, WORKSPACE)))
    print("Structure came from _data/blog_style.yml")


if __name__ == "__main__":
    main()
