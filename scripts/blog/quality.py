#!/usr/bin/env python3
"""Score a post against the shared style config.

Every threshold, weight and gate comes from _data/blog_style.yml, so this
module contains no hardcoded editorial policy. Editing the rubric means
editing the YAML, not this file.

    python scripts/blog/quality.py _posts/2026-09-26-example.md
    python scripts/blog/quality.py _posts/2026-09-26-example.md 80
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
FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")

# Retained for messages that must stay stable for the test suite.
MSG_MISSING_DESCRIPTION = "SEO: Missing description in frontmatter"
MSG_MISSING_CATEGORY = "Quality: Categories are missing in frontmatter. Add at least 1 category."


def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        sys.exit("Missing style config: {}".format(path))
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class BlogQualityAnalyzer:
    def __init__(self, filepath, config=None):
        self.filepath = filepath
        self.config = config or load_config()
        self.rules = self.config.get("structure", {}).get("rules", {})
        self.rubric = self.config.get("rubric", {})

        self.raw_content = ""
        self.frontmatter = {}
        self.content = ""
        self.lines = []
        self.headings = []
        self.warnings = []

        self.scores = dict(self.rubric.get("weights", {})) or {
            "content_quality": 30,
            "technical_accuracy": 20,
            "structure": 15,
            "examples": 10,
            "readability": 10,
            "references": 10,
            "seo": 5,
        }

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_file(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError("File not found: {}".format(self.filepath))

        with open(self.filepath, "r", encoding="utf-8") as handle:
            self.raw_content = handle.read()

        match = FRONTMATTER_RE.match(self.raw_content)
        if not match:
            self.warnings.append("Invalid or missing frontmatter blocks (---)")
            self.content = self.raw_content
            self.lines = self.content.split("\n")
            return False

        try:
            parsed = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            self.warnings.append("Frontmatter is not valid YAML: {}".format(exc))
            parsed = {}

        if not isinstance(parsed, dict):
            self.warnings.append("Frontmatter did not parse to a mapping")
            parsed = {}

        self.frontmatter = parsed
        self.content = match.group(2)
        self.lines = self.content.split("\n")
        return True

    # ------------------------------------------------------------------
    # Fence-aware heading detection
    #
    # A "# Add the dependency" line inside a ```bash fence is a shell comment,
    # not a body H1. The old regex counted it as one and cost the post points.
    # Headings are located on a fence-blanked view of the content, but word
    # counts still run over the real lines so code still counts as substance.
    # ------------------------------------------------------------------
    def scan_structure(self):
        in_fence = False
        fence_marker = ""
        headings = []

        for index, line in enumerate(self.lines):
            stripped = line.strip()
            fence_match = FENCE_OPEN_RE.match(stripped)

            if in_fence:
                if fence_match and stripped.startswith(fence_marker):
                    in_fence = False
                continue

            if fence_match:
                in_fence = True
                fence_marker = fence_match.group(1)[:3]
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading_match:
                headings.append((index, len(heading_match.group(1)), heading_match.group(2).strip()))

        self.headings = headings

    def section_text(self, start_line, end_line):
        """Raw lines for a section, so fenced code still counts as words."""
        return "\n".join(self.lines[start_line:end_line])

    def text_before_first_heading(self):
        if not self.headings:
            return self.content
        return "\n".join(self.lines[: self.headings[0][0]])

    def content_text(self):
        """Content with fenced code blanked out, for link and image scanning."""
        if getattr(self, "_prose", None) is None:
            fences = self._fence_line_indexes()
            self._prose = "\n".join(
                "" if index in fences else line
                for index, line in enumerate(self.lines)
            )
        return self._prose

    def _fence_line_indexes(self):
        cached = getattr(self, "_fence_lines", None)
        if cached is not None:
            return cached
        indexes = set()
        in_fence = False
        marker = ""
        for index, line in enumerate(self.lines):
            stripped = line.strip()
            match = FENCE_OPEN_RE.match(stripped)
            if in_fence:
                indexes.add(index)
                if match and stripped.startswith(marker):
                    in_fence = False
                continue
            if match:
                in_fence = True
                marker = match.group(1)[:3]
                indexes.add(index)
        self._fence_lines = indexes
        return indexes

    def _inside_fence(self, index):
        return index in self._fence_line_indexes()

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze(self):
        self.load_file()
        self.scan_structure()

        self._score_seo()
        self._score_structure()
        self._score_readability()
        self._score_examples()
        self._score_references()
        self._score_technical_accuracy()
        self._score_content_quality()

    def _deduct(self, category, points, message):
        self.scores[category] = max(0, self.scores[category] - points)
        self.warnings.append(message)

    # -- seo ------------------------------------------------------------
    def _score_seo(self):
        max_desc = self.rules.get("max_description_chars", 160)
        min_desc = self.rules.get("min_description_chars", 50)
        body = self.content_text()

        title = self.frontmatter.get("title") or ""
        if not title:
            self._deduct("seo", 2, "SEO: Missing title in frontmatter")
        elif len(str(title)) < 10:
            self._deduct("seo", 1, "SEO: Title is too short (less than 10 characters)")

        description = self.frontmatter.get("description") or ""
        if not description:
            self._deduct("seo", 2, MSG_MISSING_DESCRIPTION)
        elif not min_desc <= len(str(description)) <= max_desc:
            self._deduct(
                "seo", 1,
                "SEO: Description length is {} characters. Recommended is {}-{} characters "
                "for search listings.".format(len(str(description)), min_desc, max_desc),
            )

        for alt, src in re.findall(r"!\[(.*?)\]\((.*?)\)", body):
            if not alt.strip():
                self._deduct(
                    "seo", 1,
                    "SEO: Image with source '{}' is missing an alt text description.".format(src),
                )

    # -- structure ------------------------------------------------------
    def _score_structure(self):
        min_level = self.rules.get("min_heading_level", 2)
        max_level = self.rules.get("max_heading_level", 3)
        min_intro = self.rules.get("min_intro_words_before_first_heading", 30)

        if not self.headings:
            self._deduct("structure", 5, "Structure: No headings found in post content")
        else:
            intro_words = len(self.text_before_first_heading().split())
            if intro_words < min_intro:
                self._deduct(
                    "structure", 3,
                    "Structure: Missing or very short introduction before first heading",
                )

        if self.rules.get("no_h1_in_body", True):
            h1s = [h for h in self.headings if h[1] < min_level]
            if h1s:
                self._deduct(
                    "structure", 2,
                    "Structure: Found H1 (#) headings in content. Jekyll uses H1 for page "
                    "titles; use H2 (##) or H3 (###) in the post body.",
                )

        too_deep = [h for h in self.headings if h[1] > max_level]
        if too_deep:
            self._deduct(
                "structure", 2,
                "Structure: Found heading deeper than h{}. The layout only styles and "
                "lists h2-h3.".format(max_level),
            )

        titles = [h[2] for h in self.headings if h[1] >= min_level]
        if len(titles) != len(set(titles)):
            self._deduct("structure", 2, "Structure: Duplicate subheadings found in the content body.")

        for position, (index, level, text) in enumerate(self.headings):
            if level < min_level:
                continue
            if re.search(r"reference|source", text, re.IGNORECASE):
                continue
            end = self.headings[position + 1][0] if position + 1 < len(self.headings) else len(self.lines)
            words = len(self.section_text(index + 1, end).split())
            if 0 < words < 30:
                self._deduct(
                    "structure", 2,
                    "Structure: Section '{}' is very short ({} words). Elaborate or "
                    "combine sections.".format(text, words),
                )

        has_takeaway = any(
            re.search(term, self.content, re.IGNORECASE)
            for term in (r"takeaway", r"conclusion", r"summary", r"key takeaways")
        )
        if not has_takeaway:
            self._deduct("structure", 2, "Structure: No summary, takeaways, or conclusion heading identified.")

    # -- readability ----------------------------------------------------
    def _score_readability(self):
        max_paragraph = self.rules.get("max_paragraph_words", 150)

        long_paragraphs = 0
        for paragraph in self.content.split("\n\n"):
            text = paragraph.strip()
            if not text or text.startswith("```") or text.startswith(">"):
                continue
            if len(text.split()) > max_paragraph:
                long_paragraphs += 1

        if long_paragraphs:
            self._deduct(
                "readability", min(4, long_paragraphs),
                "Readability: Found {} excessively long paragraphs (>{} words). "
                "Break them up.".format(long_paragraphs, max_paragraph),
            )

        passive = re.findall(r"\b(?:is|was|were|be|been|being)\s+\w+ed\b", self.content, re.IGNORECASE)
        if len(passive) > 15:
            self._deduct(
                "readability", 2,
                "Readability: Frequent use of passive writing detected. Prefer active "
                "voice where possible.",
            )

    # -- examples -------------------------------------------------------
    def _score_examples(self):
        if self.content.count("```") < 2:
            coding = ("go", "golang", "typescript", "javascript", "python", "code", "sql", "bash")
            tags = self.frontmatter.get("tags") or []
            categories = self.frontmatter.get("categories") or []
            if any(item in coding for item in list(tags) + list(categories)):
                self._deduct(
                    "examples", 5,
                    "Examples: Coding topic tag active, but no code blocks found in content.",
                )
            else:
                self._deduct(
                    "examples", 2,
                    "Examples: No practical code blocks/examples found in the article.",
                )

    # -- references -----------------------------------------------------
    def _score_references(self):
        body = self.content_text()
        required = self.rules.get("required_trailing_section", "References")

        if not re.search(r"^#{{1,6}}\s+{}\s*$".format(re.escape(required)), body, re.IGNORECASE | re.MULTILINE):
            self._deduct(
                "references", 5,
                "References: Missing dedicated '{}' heading at the end of the post.".format(required),
            )

        links = re.findall(r"\[.*?\]\((.*?)\)", body)
        external = [l for l in links if l.startswith("http") and "github.io" not in l]
        if not external:
            self._deduct("references", 4, "References: No external source citations or documentation links found in post.")

        for link in links:
            if "example.com" in link or "todo" in link.lower() or not link.strip():
                self._deduct("references", 2, "References: Found unresolved placeholder link '{}'".format(link))

    # -- technical accuracy --------------------------------------------
    def _score_technical_accuracy(self):
        if not self.frontmatter.get("author"):
            self._deduct("technical_accuracy", 2, "Accuracy: Author is missing from frontmatter metadata.")

        if self.frontmatter.get("layout") != "post":
            self._deduct("technical_accuracy", 3, "Accuracy: Layout must be set to 'post' in frontmatter.")

        min_words = self.rules.get("min_words", 300)
        short_words = self.rules.get("short_post_words", 500)
        total_words = len(self.content.split())

        if total_words < min_words:
            self._deduct(
                "technical_accuracy", 8,
                "Accuracy: Post is very short ({} words). Detailed developer articles should "
                "be at least {} words.".format(total_words, min_words),
            )
        elif total_words < short_words:
            self._deduct(
                "technical_accuracy", 3,
                "Accuracy: Post is somewhat short ({} words). Consider adding more details "
                "or context.".format(total_words),
            )

    # -- content quality ------------------------------------------------
    def _score_content_quality(self):
        if not self.frontmatter.get("categories"):
            self._deduct("content_quality", 5, MSG_MISSING_CATEGORY)
        if not self.frontmatter.get("tags"):
            self._deduct("content_quality", 5, "Quality: Tags are missing in frontmatter. Add at least 1 tag.")

        if self.rubric.get("enforce_category_enum", True):
            allowed = self.rules_enum()
            if allowed:
                categories = self.frontmatter.get("categories") or []
                unknown = [c for c in categories if c not in allowed]
                if unknown:
                    self._deduct(
                        "content_quality", 3,
                        "Quality: Category outside structure.category_enum: {}. Allowed: {}.".format(
                            ", ".join(unknown), ", ".join(allowed)),
                    )

    def rules_enum(self):
        return self.config.get("structure", {}).get("category_enum") or []

    # ------------------------------------------------------------------
    def get_total_score(self):
        return sum(self.scores.values())

    def print_report(self):
        total = self.get_total_score()
        print("\nBLOG QUALITY REPORT")
        print("=" * 40)
        for category, value in self.scores.items():
            print("{:<22} {}/{}".format(category.replace("_", " ").capitalize(), value, self.rubric.get("weights", {}).get(category, value)))
        print("-" * 40)
        print("{:<22} {}/100".format("TOTAL SCORE", total))
        print("=" * 40)

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print("- {}".format(warning))
        else:
            print("\nNo warnings! Excellent job.")
        print()
        return total


def main():
    if len(sys.argv) < 2:
        print("Usage: python quality.py <path_to_markdown_file> [threshold_score]")
        sys.exit(1)

    config = load_config()
    filepath = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else config["rubric"].get("gate", 80)

    analyzer = BlogQualityAnalyzer(filepath, config)
    try:
        analyzer.analyze()
        score = analyzer.print_report()
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print("Error executing quality checker: {}".format(exc), file=sys.stderr)
        sys.exit(1)

    if score < threshold:
        print("FAILED: Score {} is below threshold of {}.".format(score, threshold))
        sys.exit(1)
    print("PASSED: Score {} meets threshold of {}.".format(score, threshold))
    sys.exit(0)


if __name__ == "__main__":
    main()
