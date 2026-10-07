#!/usr/bin/env python3
"""Generate assets/og-default.png, the default Open Graph / Twitter card.

There is no image library in requirements.txt and no binary asset in the repo, so
this writes the PNG directly: zlib for the compressed scanlines, struct for the
chunk headers. Text is drawn from a hand-rolled 5x7 bitmap font, because
rendering a TTF would mean pulling in a dependency the project does not have.

The card is deliberately text-light. It only has to survive being rendered at
140px wide in a timeline, so it is a brand block rather than a poster.

    python scripts/blog/make_og_image.py
"""

import os
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
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "'": ("00100", "00100", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
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


def main():
    canvas = Canvas(WIDTH, HEIGHT, NAVY_TOP)
    canvas.vertical_gradient(NAVY_TOP, NAVY_BOTTOM)

    # Accent stripe down the left edge.
    canvas.fill_rect(0, 0, 16, HEIGHT, ACCENT)

    # Faint horizontal rules, to give the flat gradient some structure.
    for y in range(120, HEIGHT - 60, 40):
        canvas.fill_rect(96, y, WIDTH - 192, 1, (45, 55, 72))

    title = "SAITEJA'S DEV BLOG"
    subtitle = "CHADASAITEJA.GITHUB.IO"

    title_scale = 8
    title_x = 96
    title_y = 250
    canvas.draw_text(title, title_x, title_y, title_scale, TEXT_PRIMARY)

    # Underline the title in the accent colour.
    title_w = Canvas.text_width(title, title_scale)
    canvas.fill_rect(title_x, title_y + GLYPH_H * title_scale + 28, title_w, 6, ACCENT)

    subtitle_scale = 3
    canvas.draw_text(
        subtitle, title_x, title_y + GLYPH_H * title_scale + 72, subtitle_scale, TEXT_MUTED
    )

    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "assets",
    )
    out_path = os.path.join(out_dir, "og-default.png")
    with open(out_path, "wb") as handle:
        handle.write(canvas.to_png())
    print("wrote {} ({}x{})".format(out_path, WIDTH, HEIGHT))


if __name__ == "__main__":
    main()
