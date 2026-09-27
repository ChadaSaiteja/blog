#!/usr/bin/env python3
"""Structural check for a post, driven by _data/blog_style.yml.

quality.py scores editorial quality. This checks the things that make a post
*structurally* identical to every other post, so drift is caught before it
ships:

  - front matter keys are known, and appear in the configured order
  - required fields are present, optional ones have no surprises
  - categories are inside structure.category_enum
  - the body obeys the heading rules
  - callouts use a marker from structure.rules.callout_syntax
  - the filename date matches the front matter date

    python scripts/blog/validate_style.py _posts/2026-09-26-example.md
    python scripts/blog/validate_style.py _posts/*.md
"""

import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Run: pip install -r requirements.txt")

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(WORKSPACE, "_data", "blog_style.yml")

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)
FILENAME_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-")
CALLOUT_RE = re.compile(r"^[>\s]*\[!([A-Za-z]+)\]", re.MULTILINE)
FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")


def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        sys.exit("Missing style config: {}".format(path))
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def strip_fences(content):
    """Blank out fenced blocks, preserving line count so indices stay valid."""
    out = []
    in_fence = False
    marker = ""
    for line in content.split("\n"):
        stripped = line.strip()
        opening = FENCE_OPEN_RE.match(stripped)
        if in_fence:
            out.append("")
            if opening and stripped.startswith(marker):
                in_fence = False
            continue
        if opening:
            in_fence = True
            marker = opening.group(1)[:3]
            out.append("")
            continue
        out.append(line)
    return out


def validate(filepath, config):
    structure = config.get("structure", {})
    rules = structure.get("rules", {})
    order = structure.get("frontmatter_order", [])
    required = set(structure.get("required", []))
    known = set(order) | required
    allowed_categories = set(structure.get("category_enum", []) or [])
    # The config writes them as GitHub Alerts markers, e.g.
    # "[!NOTE] | [!TIP] | [!WARNING]"; pull the bare names back out.
    allowed_callouts = {
        name.upper()
        for name in re.findall(r"\[!([A-Za-z]+)\]", str(rules.get("callout_syntax", "")))
    }

    errors = []
    warnings = []

    with open(filepath, "r", encoding="utf-8") as handle:
        raw = handle.read()

    match = FRONTMATTER_RE.match(raw)
    if not match:
        return ["missing or malformed front matter (--- ... ---)"], warnings

    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return ["front matter is not valid YAML: {}".format(exc)], warnings
    if not isinstance(frontmatter, dict):
        return ["front matter did not parse to a mapping"], warnings

    body = match.group(2)
    name = os.path.basename(filepath)

    # -- front matter keys -------------------------------------------
    present = [k for k in frontmatter if k in known]
    for key in frontmatter:
        if key not in known:
            errors.append("unknown front matter key '{}' (add it to structure.frontmatter_order)".format(key))

    expected = [k for k in order if k in present]
    if present != expected:
        errors.append(
            "front matter keys are out of order: got {}, expected {}".format(
                present, expected)
        )

    for key in sorted(required):
        if not frontmatter.get(key):
            errors.append("required front matter field '{}' is missing or empty".format(key))

    if frontmatter.get("layout") != "post":
        errors.append("layout must be 'post', got {!r}".format(frontmatter.get("layout")))

    # -- categories ---------------------------------------------------
    categories = frontmatter.get("categories") or []
    if not isinstance(categories, list):
        errors.append("categories must be a list, got {}".format(type(categories).__name__))
        categories = []
    if allowed_categories:
        unknown = [c for c in categories if c not in allowed_categories]
        if unknown:
            errors.append(
                "category not in structure.category_enum: {}. Allowed: {}".format(
                    ", ".join(unknown), ", ".join(sorted(allowed_categories)))
            )
    if len(categories) > 4:
        warnings.append("{} categories declared; cards only show the first two".format(len(categories)))

    tags = frontmatter.get("tags") or []
    if tags and not isinstance(tags, list):
        errors.append("tags must be a list, got {}".format(type(tags).__name__))

    # -- filename date ------------------------------------------------
    # A warning, not an error: it is a pre-existing sort-order nit, not
    # something that breaks the page.
    filename_date = FILENAME_DATE_RE.match(name)
    declared = frontmatter.get("date")
    if filename_date and declared:
        if hasattr(declared, "strftime"):
            declared = declared.strftime("%Y-%m-%d")
        declared = str(declared)
        if declared != filename_date.group(0).rstrip("-"):
            warnings.append(
                "filename date {} does not match front matter date {}. "
                "Jekyll sorts on the front matter value.".format(
                    filename_date.group(0).rstrip("-"), declared)
            )

    # -- headings -----------------------------------------------------
    lines = strip_fences(body)
    min_level = rules.get("min_heading_level", 2)
    max_level = rules.get("max_heading_level", 3)

    for number, line in enumerate(lines, start=1):
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not heading:
            continue
        level = len(heading.group(1))
        if level < min_level and rules.get("no_h1_in_body", True):
            # A second h1 breaks the document outline, so this is fatal.
            errors.append(
                "line {}: h{} in the body; the layout owns the single h1. Use h{}-h{}.".format(
                    number, level, min_level, max_level)
            )
        elif level > max_level:
            # Cosmetically fine, but it will be missing from the contents list.
            warnings.append(
                "line {}: h{} is deeper than h{} so it will not appear in the "
                "table of contents".format(number, level, max_level)
            )

    # -- callouts -----------------------------------------------------
    if allowed_callouts:
        for match_ in CALLOUT_RE.finditer(body):
            marker = match_.group(1).upper()
            if marker not in allowed_callouts:
                errors.append(
                    "unknown callout marker '[!{}]'. Allowed: {}".format(
                        marker, ", ".join("[!{}]".format(c) for c in sorted(allowed_callouts)))
                )

    # -- trailing section ---------------------------------------------
    trailing = rules.get("required_trailing_section")
    if trailing:
        headings = [
            re.match(r"^#{1,6}\s+(.*)$", line).group(1).strip()
            for line in lines
            if re.match(r"^#{1,6}\s+", line)
        ]
        if trailing.lower() not in [h.lower() for h in headings]:
            warnings.append("no '{}' heading found; it is the last section every post should have".format(trailing))

    return errors, warnings


def main():
    paths = sys.argv[1:]
    if not paths:
        print("Usage: python validate_style.py <post.md> [...]")
        return 1

    config = load_config()
    failed = False

    for path in paths:
        if not os.path.isabs(path):
            candidate = os.path.join(WORKSPACE, path)
            path = candidate if os.path.exists(candidate) else os.path.abspath(path)

        if not os.path.exists(path):
            print("FAIL {}: file not found".format(path))
            failed = True
            continue

        errors, warnings = validate(path, config)
        label = os.path.basename(path)

        if errors:
            failed = True
            print("FAIL {}".format(label))
            for error in errors:
                print("  error: {}".format(error))
        else:
            print("OK   {}".format(label))

        for warning in warnings:
            print("  warn:  {}".format(warning))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
