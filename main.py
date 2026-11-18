#!/usr/bin/env python3
"""make.fun news-image-20261117 entry: "The World in One Image".

A newspaper-style front-page infographic (1024x1024 PNG) summing up the
world news of Tuesday 17 November 2026. Pure Python 3.13 standard library:
a hand-built 5x7 bitmap font (glyphs stored as integer bit rows), vector
shapes drawn onto a raw RGB buffer, and a minimal PNG encoder using zlib.
No network, no files read, fully deterministic: two runs produce
byte-identical output.

Stories (all first reported on Tuesday 17 November 2026):
  * Ukraine: Ukrainian strike on the Kerch Bridge to Crimea collapsed a
    road span; Russia hit Kyiv's North and South bridges over the Dnipro,
    disrupting heating, water and power.
  * The Gulf: Iran's Revolutionary Guards fired drones at a US military
    radar at Sheikh Isa base in Bahrain (intercepted, no casualties);
    IRGC said two tankers hit mines in the Strait of Hormuz; a third US
    aircraft carrier, USS Theodore Roosevelt, arrived in the Middle East.
  * Asia: President Trump arrived in Manila for the ASEAN summit, signed
    a joint trade statement with Thailand, on a three-day Asia trip ending
    in China with talks with Xi Jinping and Vladimir Putin.
  * Space: a ULA Vulcan rocket failed in flight, destroying 40 Amazon Leo
    internet satellites.
  * Tech: Nvidia reported earnings after Tuesday's close, its first since
    CEO Jensen Huang resigned.
  * US banking: JPMorgan Chase blamed a software bug, not a cyberattack,
    for Monday's outage hitting online banking, branches and Zelle.
  * US defence: the Pentagon failed its financial audit for the ninth
    year in a row.
  * Also: Britain sanctioned eight Israeli settlement firms; the UK,
    Australia, Canada and Italy jointly urged Israel to open Gaza
    crossings for aid; Japan scrambled fighter jets after two suspected
    Russian aircraft violated its airspace; Gerard Depardieu pleaded
    guilty to a sexual assault charge in a Paris court; the EU charged
    Temu for not doing enough to stop illegal product sales.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 242, 233)
INK = (20, 20, 26)
NAVY = (16, 30, 60)
NAVY_LT = (44, 66, 108)
RED = (176, 32, 32)
BLUE = (28, 88, 158)
SKY = (158, 200, 228)
SEA = (22, 74, 124)
TEAL = (0, 118, 108)
GOLD = (196, 146, 26)
ORANGE = (230, 114, 22)
YELLOW = (246, 198, 58)
GREY = (94, 94, 100)
WHITE = (255, 255, 255)
GREEN = (32, 126, 64)
DARKGREY = (64, 64, 72)

# ------------------------------------------------------- 5x7 bitmap font
# Glyphs as 7 rows of 5 bits, stored as integers (bit 4 = leftmost pixel).
# Uppercase, digits and common punctuation only; text is uppercased.
FONT = {
    'A': (14, 17, 17, 31, 17, 17, 17),
    'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (14, 17, 16, 16, 16, 17, 14),
    'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (14, 17, 16, 23, 17, 17, 15),
    'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14),
    'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17),
    'N': (17, 25, 21, 19, 17, 17, 17),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14),
    'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 27, 17),
    'X': (17, 17, 10, 4, 10, 17, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4),
    'Z': (31, 1, 2, 4, 8, 16, 31),
    '0': (14, 17, 19, 21, 25, 17, 14),
    '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 6, 8, 16, 31),
    '3': (31, 2, 4, 2, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2),
    '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (6, 8, 16, 30, 17, 17, 14),
    '7': (31, 1, 2, 4, 8, 8, 8),
    '8': (14, 17, 17, 14, 17, 17, 14),
    '9': (14, 17, 17, 15, 1, 2, 12),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 12, 12),
    ',': (0, 0, 0, 0, 12, 4, 8),
    '-': (0, 0, 0, 14, 0, 0, 0),
    "'": (4, 4, 8, 0, 0, 0, 0),
    ':': (0, 12, 12, 0, 12, 12, 0),
    ';': (0, 12, 12, 0, 12, 4, 8),
    '/': (1, 2, 2, 4, 8, 8, 16),
    '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8),
    '%': (25, 26, 2, 4, 8, 11, 19),
    '!': (4, 4, 4, 4, 4, 0, 4),
    '?': (14, 17, 1, 6, 4, 0, 4),
    '+': (0, 4, 4, 31, 4, 4, 0),
    '=': (0, 0, 31, 0, 31, 0, 0),
    '_': (0, 0, 0, 0, 0, 0, 31),
    '*': (0, 4, 21, 14, 21, 4, 0),
    '$': (4, 15, 20, 14, 5, 30, 4),
    '&': (12, 18, 20, 8, 21, 18, 13),
    '"': (10, 10, 10, 0, 0, 0, 0),
}

BLANK = (0, 0, 0, 0, 0, 0, 0)


def glyph_rows(ch):
    return FONT.get(ch.upper(), BLANK)


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, scale, max_width):
    """Greedy word wrap; returns lines of at most max_width pixels."""
    per_line = max(1, (max_width + scale) // (6 * scale))
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) <= per_line:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            while len(word) > per_line:
                lines.append(word[:per_line])
                word = word[per_line:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ canvas
class Canvas:
    """Raw RGB buffer with filled shapes and bitmap text."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.box(0, 0, w, h, bg)

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def box(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def frame(self, x, y, w, h, c, t=1):
        self.box(x, y, w, t, c)
        self.box(x, y + h - t, w, t, c)
        self.box(x, y, t, h, c)
        self.box(x + w - t, y, t, h, c)

    def hline(self, x0, x1, y, c, t=1):
        self.box(x0, y, x1 - x0, t, c)

    def vline(self, x, y0, y1, c, t=1):
        self.box(x, y0, t, y1 - y0, c)

    def segment(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        while True:
            self.put(x, y, c)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.box(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for k in range(t):
            rr = r - k
            for a in range(360):
                rad = math.radians(a)
                self.put(cx + int(rr * math.cos(rad)),
                         cy + int(rr * math.sin(rad)), c)

    def tri(self, p1, p2, p3, c):
        xs = sorted([p1, p2, p3], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = xs
        for y in range(y0, y2 + 1):
            def interp(ax, ay, bx, by):
                return ax + (bx - ax) * (y - ay) / (by - ay) if by != ay else ax
            xa = interp(x0, y0, x1, y1)
            xb = interp(x0, y0, x2, y2)
            xc = interp(x1, y1, x2, y2) if y >= y1 else xa
            lo, hi = int(min(xa, xb, xc)), int(max(xa, xb, xc))
            self.box(lo, y, hi - lo + 1, 1, c)

    def glyph(self, x, y, ch, scale, c):
        for ry, bits in enumerate(glyph_rows(ch)):
            for rx in range(5):
                if bits & (1 << (4 - rx)):
                    self.box(x + rx * scale, y + ry * scale,
                             scale, scale, c)

    def text(self, x, y, s, scale, c):
        for ch in s:
            self.glyph(x, y, ch, scale, c)
            x += 6 * scale
        return x

    def text_center(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)

    def para(self, x, y, s, scale, c, max_width, lh=None):
        """Draw a wrapped paragraph; returns y just below the last line."""
        lh = lh or (9 * scale)
        for line in wrap_text(s, scale, max_width):
            self.text(x, y, line, scale, c)
            y += lh
        return y


# -------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_png(cv):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    return png


# ------------------------------------------------------------------- icons
def burst(cv, cx, cy, r, c_core, c_ring):
    """Starburst: radiating spokes plus a solid core."""
    for ang in range(0, 360, 20):
        rad = math.radians(ang)
        cv.segment(cx, cy, cx + int(r * math.cos(rad)),
                   cy + int(r * math.sin(rad)), c_ring)
    cv.disc(cx, cy, r // 2, c_core)
    cv.disc(cx, cy, r // 4, c_ring)


def icon_radar(cv, x, y, s):
    """Radar dish with sweeping beam and incoming drones."""
    cv.ring(x + 26 * s // 10, y + 30 * s // 10, 18 * s // 10, INK, 3)
    cv.disc(x + 26 * s // 10, y + 30 * s // 10, 5 * s // 10, RED)
    cv.segment(x + 26 * s // 10, y + 30 * s // 10,
               x + 44 * s // 10, y + 12 * s // 10, RED)
    cv.box(x + 22 * s // 10, y + 48 * s // 10, 8 * s // 10, 8 * s // 10, INK)
    # Two small drones top-right.
    for dx, dy in ((46, 2), (54, 10)):
        cv.box(x + dx * s // 10, y + dy * s // 10, 8 * s // 10,
               3 * s // 10, DARKGREY)


def icon_handshake(cv, x, y, s):
    """Two flags on poles above a clasped-hands bar."""
    cv.box(x + 6 * s // 10, y + 4 * s // 10, 3 * s // 10, 34 * s // 10, INK)
    cv.box(x + 42 * s // 10, y + 4 * s // 10, 3 * s // 10, 34 * s // 10, INK)
    cv.box(x + 9 * s // 10, y + 4 * s // 10, 16 * s // 10, 12 * s // 10, BLUE)
    cv.box(x + 9 * s // 10, y + 8 * s // 10, 16 * s // 10, 3 * s // 10, WHITE)
    cv.box(x + 45 * s // 10, y + 4 * s // 10, 16 * s // 10, 12 * s // 10, RED)
    cv.box(x + 45 * s // 10, y + 8 * s // 10, 16 * s // 10, 3 * s // 10, WHITE)
    cv.box(x + 10 * s // 10, y + 42 * s // 10, 60 * s // 10, 12 * s // 10, GOLD)
    cv.text(x + 15 * s // 10, y + 44 * s // 10, "ASEAN", 1, INK)


def icon_rocket(cv, x, y, s):
    """Rocket climbing, with falling satellite debris below."""
    bx, by = x + 30 * s // 10, y + 14 * s // 10
    cv.tri((bx, by - 12 * s // 10), (bx - 9 * s // 10, by + 8 * s // 10),
           (bx + 9 * s // 10, by + 8 * s // 10), INK)
    cv.box(bx - 9 * s // 10, by + 8 * s // 10, 18 * s // 10, 14 * s // 10, RED)
    cv.tri((bx - 16 * s // 10, by + 26 * s // 10),
           (bx - 9 * s // 10, by + 10 * s // 10),
           (bx - 9 * s // 10, by + 26 * s // 10), ORANGE)
    cv.tri((bx + 16 * s // 10, by + 26 * s // 10),
           (bx + 9 * s // 10, by + 10 * s // 10),
           (bx + 9 * s // 10, by + 26 * s // 10), ORANGE)
    cv.disc(bx, by + 32 * s // 10, 5 * s // 10, ORANGE)
    cv.disc(bx, by + 40 * s // 10, 3 * s // 10, YELLOW)
    # Debris: small squares tumbling down-left.
    for dx, dy in ((2, 44), (10, 52), (48, 48), (56, 40)):
        cv.box(x + dx * s // 10, y + dy * s // 10, 5 * s // 10,
               5 * s // 10, GREY)


def icon_chip(cv, x, y, s):
    """Microchip with pins, green up-arrow for earnings day."""
    cv.box(x + 10 * s // 10, y + 10 * s // 10, 40 * s // 10, 40 * s // 10, INK)
    cv.box(x + 18 * s // 10, y + 18 * s // 10, 24 * s // 10, 24 * s // 10,
           NAVY_LT)
    cv.text(x + 22 * s // 10, y + 24 * s // 10, "NV", 2, WHITE)
    for i in range(4):
        px = x + (14 + i * 11) * s // 10
        cv.box(px, y, 4 * s // 10, 10 * s // 10, INK)
        cv.box(px, y + 50 * s // 10, 4 * s // 10, 10 * s // 10, INK)
        cv.box(x, y + (14 + i * 11) * s // 10, 10 * s // 10, 4 * s // 10, INK)
        cv.box(x + 50 * s // 10, y + (14 + i * 11) * s // 10, 10 * s // 10,
               4 * s // 10, INK)
    # Small green arrow rising at the top-right.
    ax = x + 52 * s // 10
    cv.segment(ax, y + 20 * s // 10, ax, y + 2 * s // 10, GREEN)
    cv.tri((ax - 5 * s // 10, y + 8 * s // 10),
           (ax + 5 * s // 10, y + 8 * s // 10),
           (ax, y - 2 * s // 10), GREEN)


def icon_bank(cv, x, y, s):
    """Bank facade with a red bug (software bug, not a hack)."""
    cv.tri((x + 6 * s // 10, y + 14 * s // 10),
           (x + 54 * s // 10, y + 14 * s // 10),
           (x + 30 * s // 10, y + 2 * s // 10), NAVY)
    cv.box(x + 8 * s // 10, y + 16 * s // 10, 44 * s // 10, 26 * s // 10,
           WHITE)
    cv.frame(x + 8 * s // 10, y + 16 * s // 10, 44 * s // 10, 26 * s // 10,
             INK, 2)
    for i in range(3):
        cv.box(x + (14 + i * 13) * s // 10, y + 20 * s // 10, 5 * s // 10,
               18 * s // 10, NAVY_LT)
    cv.box(x + 8 * s // 10, y + 42 * s // 10, 44 * s // 10, 4 * s // 10, INK)
    # Bug: red dot with legs, bottom-right.
    bx, by = x + 52 * s // 10, y + 50 * s // 10
    cv.disc(bx, by, 5 * s // 10, RED)
    for ang in (45, 135, 225, 315):
        rad = math.radians(ang)
        cv.segment(bx, by, bx + int(9 * s // 10 * math.cos(rad)),
                   by + int(9 * s // 10 * math.sin(rad)), RED)


def icon_ledger(cv, x, y, s):
    """Audit ledger with a big red X over the balance line."""
    cv.box(x + 6 * s // 10, y + 4 * s // 10, 48 * s // 10, 52 * s // 10, WHITE)
    cv.frame(x + 6 * s // 10, y + 4 * s // 10, 48 * s // 10, 52 * s // 10,
             INK, 2)
    for i in range(4):
        yy = y + (12 + i * 10) * s // 10
        cv.box(x + 12 * s // 10, yy, 26 * s // 10, 3 * s // 10, GREY)
    cv.box(x + 42 * s // 10, y + 42 * s // 10, 6 * s // 10, 3 * s // 10, RED)
    cv.segment(x + 42 * s // 10, y + 12 * s // 10, x + 54 * s // 10,
               y + 24 * s // 10, RED)
    cv.segment(x + 54 * s // 10, y + 12 * s // 10, x + 42 * s // 10,
               y + 24 * s // 10, RED)


# ------------------------------------------------------------------- layout
def story_panel(cv, x, y, w, h, tag, tag_c, headline, body, icon):
    cv.box(x, y, w, h, WHITE)
    cv.frame(x, y, w, h, INK, 2)
    cv.box(x, y, w, 30, tag_c)
    cv.text(x + 10, y + 8, tag, 2, WHITE)
    yy = cv.para(x + 12, y + 38, headline, 3, NAVY, w - 24, lh=28)
    body_y = yy + 6
    max_lines = max(1, (y + h - 48 - body_y) // 17)
    for line in wrap_text(body, 2, w - 24)[:max_lines]:
        cv.text(x + 12, body_y, line, 2, INK)
        body_y += 17
    icon(cv, x + w - 52, y + h - 46, 6)


def hero_bridge(cv, x, y, w, h):
    """Kerch Bridge over the strait: deck, a collapsed middle span,
    a blast burst, and water below."""
    cv.box(x, y, w, h, SKY)
    # Sun and clouds.
    cv.disc(x + w - 52, y + 34, 20, YELLOW)
    cv.disc(x + 60, y + 30, 14, WHITE)
    cv.disc(x + 82, y + 24, 18, WHITE)
    cv.disc(x + 104, y + 32, 12, WHITE)
    # Bridge deck: two intact spans, a gap in the middle.
    deck_y = y + 108
    cv.box(x, deck_y, 120, 10, INK)
    cv.box(x + w - 120, deck_y, 120, 10, INK)
    # Pylons.
    cv.box(x + 96, deck_y + 10, 10, 74, INK)
    cv.box(x + w - 106, deck_y + 10, 10, 74, INK)
    # Cables from the pylons.
    cv.segment(x + 101, deck_y, x + 20, deck_y - 52, INK)
    cv.segment(x + 101, deck_y, x + 116, deck_y - 44, INK)
    cv.segment(x + w - 101, deck_y, x + w - 20, deck_y - 52, INK)
    cv.segment(x + w - 101, deck_y, x + w - 116, deck_y - 44, INK)
    # Collapsed span: tilted slabs falling into the water.
    cv.segment(x + 128, deck_y + 4, x + 176, deck_y + 62, INK)
    cv.segment(x + 128, deck_y + 12, x + 176, deck_y + 70, INK)
    cv.segment(x + w - 128, deck_y + 4, x + w - 176, deck_y + 62, INK)
    cv.segment(x + w - 128, deck_y + 12, x + w - 176, deck_y + 70, INK)
    # Blast burst where the span gave way.
    burst(cv, x + w // 2, deck_y - 6, 44, YELLOW, ORANGE)
    # Water.
    cv.box(x, y + h - 56, w, 56, SEA)
    for i in range(5):
        wx = x + 24 + i * 66
        cv.segment(wx, y + h - 34, wx + 34, y + h - 34, WHITE)
        cv.segment(wx + 10, y + h - 20, wx + 44, y + h - 20, WHITE)
    cv.text(x + 12, y + h - 46, "KERCH BRIDGE, CRIMEA", 2, WHITE)


def build():
    cv = Canvas(W, H, PAPER)
    cv.frame(6, 6, W - 12, H - 12, NAVY, 4)

    # Masthead.
    cv.box(14, 14, W - 28, 104, NAVY)
    cv.text_center(W // 2, 30, "THE WORLD IN ONE IMAGE", 5, WHITE)
    cv.text_center(W // 2, 82, "TUESDAY, 17 NOVEMBER 2026", 3, GOLD)
    cv.hline(14, W - 14, 122, RED, 5)

    # Lead story: the Kerch Bridge.
    cv.box(24, 132, 976, 252, WHITE)
    cv.frame(24, 132, 976, 252, INK, 2)
    cv.text(40, 146, "LEAD STORY - UKRAINE", 2, RED)
    cv.text(40, 176, "KERCH BRIDGE FALLS", 5, NAVY)
    cv.para(40, 226, "UKRAINE STRUCK THE BRIDGE TO CRIMEA; A ROAD SPAN "
            "COLLAPSED INTO THE STRAIT.", 2, INK, 540, lh=20)
    cv.para(40, 272, "RUSSIA HIT KYIV'S TWO DNIPRO BRIDGES, CUTTING "
            "HEAT, WATER AND POWER.", 2, INK, 540, lh=20)
    cv.para(40, 318, "THE WAR'S LONGEST-LIVED SYMBOL, BROKEN IN A DAY.",
            2, INK, 540, lh=20)
    hero_bridge(cv, 620, 146, 364, 224)

    # Middle row.
    y1, h1 = 400, 220
    story_panel(cv, 24, y1, 314, h1, "THE GULF", RED,
                "IRAN HITS US RADAR IN BAHRAIN",
                "IRAN FIRED DRONES AT THE US RADAR IN BAHRAIN; ALL "
                "INTERCEPTED. TWO TANKERS HIT MINES IN HORMUZ.",
                icon_radar)
    story_panel(cv, 355, y1, 314, h1, "ASIA - ASEAN", BLUE,
                "TRUMP LANDS IN MANILA",
                "TRADE STATEMENT SIGNED WITH THAILAND AT THE ASEAN "
                "SUMMIT; NEXT, CHINA FOR XI AND PUTIN TALKS.",
                icon_handshake)
    story_panel(cv, 686, y1, 314, h1, "SPACE", NAVY,
                "VULCAN FAILS, 40 SATELLITES LOST",
                "VULCAN ROCKET FAILED IN FLIGHT; 40 AMAZON LEO "
                "SATELLITES LOST.",
                icon_rocket)

    # Lower row.
    y2, h2 = 636, 216
    story_panel(cv, 24, y2, 314, h2, "TECH - NVIDIA", INK,
                "NVIDIA REPORTS AFTER THE BELL",
                "FIRST EARNINGS SINCE CEO JENSEN HUANG RESIGNED. THE "
                "MARKET WATCHES ITS AI CHIP SALES.",
                icon_chip)
    story_panel(cv, 355, y2, 314, h2, "US - BANKING", TEAL,
                "JPMORGAN BLAMES SOFTWARE BUG",
                "MONDAY'S OUTAGE HIT ONLINE BANKING, BRANCHES AND "
                "ZELLE. A BUG, NOT A CYBERATTACK, THE BANK SAYS.",
                icon_bank)
    story_panel(cv, 686, y2, 314, h2, "US - DEFENCE", DARKGREY,
                "PENTAGON FAILS AUDIT AGAIN",
                "THE US DEFENCE DEPARTMENT FAILED ITS FINANCIAL AUDIT "
                "FOR THE NINTH YEAR IN A ROW.",
                icon_ledger)

    # Ticker: also today.
    cv.box(24, 868, 976, 96, NAVY)
    cv.text(40, 878, "ALSO TODAY:", 2, GOLD)
    cv.para(40, 902, "BRITAIN SANCTIONED 8 ISRAELI SETTLEMENT FIRMS - "
            "UK, AUSTRALIA, CANADA, ITALY URGED ISRAEL TO OPEN GAZA "
            "CROSSINGS - JAPAN SCRAMBLED JETS OVER SUSPECTED RUSSIAN "
            "INCURSION - DEPARDIEU PLEADED GUILTY - EU CHARGED TEMU",
            2, WHITE, 944, lh=17)
    cv.text_center(W // 2, 974,
                   "TUESDAY, 17 NOVEMBER 2026  -  SOURCES: REUTERS, AP, BBC",
                   2, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
