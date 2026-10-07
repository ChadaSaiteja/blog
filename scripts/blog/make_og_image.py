#!/usr/bin/env python3
"""Generate the Open Graph / Twitter cards for the blog.

There is no image library in requirements.txt and no binary asset in the repo, so
this writes the PNG directly: zlib for the compressed scanlines, struct for the
chunk headers. Text is drawn from a hand-rolled 5x7 bitmap font, because
rendering a TTF would mean pulling in a dependency the project does not have.

Two cards are produced:

  og-default.png   the site-wide fallback used when a post declares no image
  og/<slug>.png    one per post, titled with the post itself

A single shared card caps social click-through, because every link in a timeline
looks identical. One card per post fixes that.

    python scripts/blog/make_og_image.py
"""

import glob
import io
import os
import re
import struct
import zlib

WIDTH = 1200
HEIGHT = 630

# Matches the accent token in _data/blog_style.yml.
NAVY_TOP = (15, 23, 42)
NAVY_BOTTOM = (30, 41, 59)
ACCENT = (37, 99, 235)
TEXT_PRIMARY = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)

# 5x7 bitmap font, uppercase only. Each glyph is 7 rows of 5 columns, '#' = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10001", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "'": ("00100", "00100", "00000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "01100", "01000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "\\": ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "#": ("01010", "11111", "01010", "01010", "11111", "01010", "00000"),
    "@": ("01110", "10001", "10111", "10101", "10111", "10000", "01110"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}

GLYPH_W = 5
GLYPH_H = 7


class Canvas:
    """A plain RGB byte canvas with just the two primitives this needs."""

    def __init__(self, width, height, fill):
        self.width = width
        self.height = height
        self.rows = [bytearray(fill * width) for _ in range(height)]

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = x * 3
            row = self.rows[y]
            row[offset] = colour[0]
            row[offset + 1] = colour[1]
            row[offset + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        for py in range(y, y + h):
            if not (0 <= py < self.height):
                continue
            row = self.rows[py]
            for px in range(x, x + w):
                if 0 <= px < self.width:
                    offset = px * 3
                    row[offset] = colour[0]
                    row[offset + 1] = colour[1]
                    row[offset + 2] = colour[2]

    def vertical_gradient(self, top, bottom):
        span = max(self.height - 1, 1)
        for y in range(self.height):
            t = y / span
            colour = tuple(
                int(round(top[i] + (bottom[i] - top[i]) * t)) for i in range(3)
            )
            offset_row = self.rows[y]
            for px in range(self.width):
                offset = px * 3
                offset_row[offset] = colour[0]
                offset_row[offset + 1] = colour[1]
                offset_row[offset + 2] = colour[2]

    def draw_text(self, text, x, y, scale, colour):
        cursor = x
        for char in text.upper():
            glyph = FONT.get(char, FONT[" "])
            for row_index, row_bits in enumerate(glyph):
                for col_index, bit in enumerate(row_bits):
                    if bit != "1":
                        continue
                    self.fill_rect(
                        cursor + col_index * scale,
                        y + row_index * scale,
                        scale,
                        scale,
                        colour,
                    )
            cursor += (GLYPH_W + 1) * scale
        return cursor

    @staticmethod
    def text_width(text, scale):
        return len(text) * (GLYPH_W + 1) * scale

    def wrap(self, text, scale, max_width):
        """Greedy word wrap against the measured pixel width."""
        words = text.split()
        lines, current = [], ""
        for word in words:
            candidate = word if not current else current + " " + word
            if self.text_width(candidate, scale) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def to_png(self):
        raw = bytearray()
        for row in self.rows:
            raw.append(0)  # filter type 0 (None) for every scanline
            raw.extend(row)
        return build_png(self.width, self.height, bytes(raw))


def chunk(tag, payload):
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def build_png(width, height, raw):
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


MARGIN = 96


def render_card(title, subtitle, eyebrow):
    """Build one 1200x630 card.

    The title is word-wrapped to at most three lines and the scale steps down
    until it fits, because the post titles range from 33 to 96 characters and a
    single fixed size either clips or wastes half the canvas.
    """
    canvas = Canvas(WIDTH, HEIGHT, NAVY_TOP)
    canvas.vertical_gradient(NAVY_TOP, NAVY_BOTTOM)

    # Accent stripe down the left edge.
    canvas.fill_rect(0, 0, 16, HEIGHT, ACCENT)

    # Faint horizontal rules, to give the flat gradient some structure.
    for y in range(120, HEIGHT - 60, 40):
        canvas.fill_rect(MARGIN, y, WIDTH - MARGIN * 2, 1, (45, 55, 72))

    canvas.draw_text(eyebrow.upper(), MARGIN, 96, 3, TEXT_MUTED)

    max_w = WIDTH - MARGIN * 2

    chosen = None
    for scale in (8, 7, 6, 5, 4, 3):
        lines = canvas.wrap(title, scale, max_w)
        if len(lines) <= 3:
            chosen = (scale, lines)
            break
    if chosen is None:
        chosen = (3, canvas.wrap(title, 3, max_w))

    scale, lines = chosen
    line_h = GLYPH_H * scale
    gap = max(6, scale * 3)
    block_h = line_h * len(lines) + gap * (len(lines) - 1)

    title_y = max(210, (HEIGHT - block_h) // 2 - 60)
    for i, line in enumerate(lines):
        canvas.draw_text(line, MARGIN, title_y + i * (line_h + gap), scale, TEXT_PRIMARY)

    rule_y = title_y + block_h + 28
    rule_w = min(max_w, max(canvas.text_width(l, scale) for l in lines))
    canvas.fill_rect(MARGIN, rule_y, rule_w, 6, ACCENT)

    canvas.draw_text(subtitle.upper(), MARGIN, rule_y + 34, 3, TEXT_MUTED)
    return canvas


def slug_from_filename(name):
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.splitext(name)[0])


def read_post_titles(posts_dir):
    """Pull title and description out of each post's front matter.

    Deliberately a regex over the front matter rather than a YAML parse: this
    script runs with a bare python and PyYAML is only a dev dependency.
    """
    out = []
    for path in sorted(glob.glob(os.path.join(posts_dir, "*.md"))):
        raw = io.open(path, encoding="utf-8").read()
        if not raw.startswith("---"):
            continue
        block = raw.split("---", 2)[1]

        def field(key):
            m = re.search(r'^%s:\s*"?(.*?)"?\s*$' % key, block, re.M)
            return m.group(1) if m else ""

        title = field("title")
        if not title or field("draft") == "true":
            continue
        out.append((slug_from_filename(os.path.basename(path)), title))
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets = os.path.join(root, "assets")
    og_dir = os.path.join(assets, "og")

    default = render_card("Saiteja's Dev Blog", "chadasaiteja.github.io/blog", "Engineering Blog")
    default_path = os.path.join(assets, "og-default.png")
    with open(default_path, "wb") as handle:
        handle.write(default.to_png())
    print("wrote %s" % os.path.relpath(default_path, root))

    if not os.path.isdir(og_dir):
        os.makedirs(og_dir)

    posts = read_post_titles(os.path.join(root, "_posts"))
    for slug, title in posts:
        # Descriptions carry commas and full stops that read badly on a card,
        # so the eyebrow is the primary category instead.
        card = render_card(title, "chadasaiteja.github.io/blog", "Article")
        path = os.path.join(og_dir, slug + ".png")
        with open(path, "wb") as handle:
            handle.write(card.to_png())
        print("wrote %s" % os.path.relpath(path, root))

    print("\n%d post cards + 1 default" % len(posts))
    print("Add `image: /assets/og/<slug>.png` to a post's front matter to use it.")


if __name__ == "__main__":
    main()
