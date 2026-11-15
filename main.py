# DOWN IS UP! -- make.fun ai-excited-01 entry (b)
#
# One image, drawn from scratch in pure Python 3.13 stdlib:
# a city hangs upside-down from the top of the sky, and a rocket
# dives DOWN toward it while the dawn sky waits below. The joke
# of the picture is the headline: down is up.
#
# Output: exactly one file, /output/entry.png
# (or $MAKEFUN_OUTPUT_DIR/entry.png when that is set).
# 1024x1024, deterministic: same bytes on every run.

import os
import random
import struct
import zlib
from math import sqrt

W = 1024
H = 1024

OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
OUT_PATH = os.path.join(OUT_DIR, "entry.png")

# Fixed seed: every run draws the identical picture.
rng = random.Random(20261116)


# ---------------------------------------------------------------- PNG out

def _chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(
        ">I", zlib.crc32(body) & 0xFFFFFFFF
    )


def save_png(rows):
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    blob = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "wb") as fh:
        fh.write(blob)


# ---------------------------------------------------------------- canvas

# rows[y] is a bytearray of W*3 RGB bytes.
rows = [bytearray(W * 3) for _ in range(H)]


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def dot(x, y, col):
    if 0 <= x < W and 0 <= y < H:
        i = x * 3
        rows[y][i] = col[0]
        rows[y][i + 1] = col[1]
        rows[y][i + 2] = col[2]


def mix(x, y, col, a):
    """Blend col over the pixel at (x, y) with weight a (0..1)."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        i = x * 3
        r = rows[y]
        r[i] = int(r[i] + (col[0] - r[i]) * a)
        r[i + 1] = int(r[i + 1] + (col[1] - r[i + 1]) * a)
        r[i + 2] = int(r[i + 2] + (col[2] - r[i + 2]) * a)


def rect(x0, y0, x1, y1, col):
    x0 = _clamp(x0, 0, W)
    x1 = _clamp(x1, 0, W)
    y0 = _clamp(y0, 0, H)
    y1 = _clamp(y1, 0, H)
    if x1 <= x0 or y1 <= y0:
        return
    fill = bytes(col) * (x1 - x0)
    for y in range(y0, y1):
        rows[y][x0 * 3 : x1 * 3] = fill


def disc(cx, cy, r, col):
    for dy in range(-r, r + 1):
        dx = int(sqrt(r * r - dy * dy))
        rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, col)


def disc_mix(cx, cy, r, col, a):
    for dy in range(-r, r + 1):
        dx = int(sqrt(r * r - dy * dy))
        for x in range(cx - dx, cx + dx + 1):
            mix(x, cy + dy, col, a)


def ellipse(cx, cy, rx, ry, col):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * sqrt(t)) if t > 0 else 0
        rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, col)


def ellipse_mix(cx, cy, rx, ry, col, a):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * sqrt(t)) if t > 0 else 0
        for x in range(cx - dx, cx + dx + 1):
            mix(x, cy + dy, col, a)


def poly(points, col):
    """Scanline fill of a simple polygon given as [(x, y), ...]."""
    ys = [p[1] for p in points]
    top, bot = min(ys), max(ys)
    n = len(points)
    for y in range(top, bot + 1):
        hits = []
        for k in range(n):
            ax, ay = points[k]
            bx, by = points[(k + 1) % n]
            if (ay <= y < by) or (by <= y < ay):
                t = (y - ay) / float(by - ay)
                hits.append(ax + t * (bx - ax))
        hits.sort()
        for k in range(0, len(hits) - 1, 2):
            rect(int(hits[k]), y, int(hits[k + 1]) + 1, y + 1, col)


def lerp3(c0, c1, t):
    return (
        int(c0[0] + (c1[0] - c0[0]) * t),
        int(c0[1] + (c1[1] - c0[1]) * t),
        int(c0[2] + (c1[2] - c0[2]) * t),
    )


# ---------------------------------------------------------------- sky

# Night indigo at the top, melting into a burning dawn at the bottom:
# the sky gets brighter the further DOWN you look, because down is up.
SKY_STOPS = [
    (0.00, (8, 12, 38)),
    (0.30, (30, 20, 74)),
    (0.52, (96, 38, 110)),
    (0.72, (214, 96, 74)),
    (1.00, (255, 172, 84)),
]


def paint_sky():
    for y in range(H):
        t = y / float(H - 1)
        for k in range(len(SKY_STOPS) - 1):
            p0, c0 = SKY_STOPS[k]
            p1, c1 = SKY_STOPS[k + 1]
            if p0 <= t <= p1:
                col = lerp3(c0, c1, (t - p0) / (p1 - p0))
                break
        else:
            col = SKY_STOPS[-1][1]
        rows[y][:] = bytes(col) * W


def paint_stars():
    for _ in range(260):
        x = rng.randrange(0, W)
        y = int((rng.random() ** 1.6) * 640)
        tone = rng.random()
        if tone < 0.6:
            col = (255, 255, 255)
        elif tone < 0.8:
            col = (255, 240, 200)
        else:
            col = (180, 220, 255)
        if rng.random() < 0.22:
            rect(x, y, x + 2, y + 2, col)
        else:
            dot(x, y, col)
    # A few bright sparkle stars with a cross glint.
    for _ in range(12):
        x = rng.randrange(40, W - 40)
        y = rng.randrange(20, 420)
        col = (255, 250, 230)
        rect(x - 4, y, x + 5, y + 1, col)
        rect(x, y - 4, x + 1, y + 5, col)
        dot(x, y, (255, 255, 255))


def paint_clouds():
    # Soft dawn clouds drifting low, plus two thin high ones.
    puffs = [
        (180, 760, 150, 26, 0.20),
        (700, 820, 190, 30, 0.22),
        (880, 700, 120, 22, 0.18),
        (120, 880, 130, 24, 0.20),
        (480, 940, 170, 26, 0.16),
        (300, 330, 130, 16, 0.14),
        (760, 300, 110, 14, 0.12),
    ]
    for cx, cy, rx, ry, a in puffs:
        ellipse_mix(cx, cy, rx, ry, (255, 205, 165), a)
        ellipse_mix(cx, cy - 8, int(rx * 0.6), int(ry * 0.7), (255, 225, 195), a)


# ---------------------------------------------------------------- the city in the sky

NEON = [(110, 230, 255), (255, 120, 200), (255, 196, 90), (140, 255, 190)]
LIT = [(255, 196, 90), (110, 230, 255), (255, 120, 200), (255, 240, 200)]


def paint_city():
    """Skyscrapers hang from the top edge, pointing DOWN at the viewer."""
    towers = []
    x = 14
    while x < 990:
        w = rng.randrange(56, 132)
        h = rng.randrange(150, 470)
        body = (
            12 + rng.randrange(0, 11),
            15 + rng.randrange(0, 9),
            42 + rng.randrange(0, 24),
        )
        towers.append((x, w, h, body))
        x += w + rng.randrange(4, 18)

    for (bx, w, h, body) in towers:
        rect(bx, 0, bx + w, h, body)
        # Lit windows: a grid, some dark, some glowing warm / cyan / pink.
        cols = max(2, w // 18)
        rows_n = max(4, h // 24)
        for ci in range(cols):
            for ri in range(rows_n):
                if rng.random() < 0.42:
                    wx = bx + 6 + ci * 18
                    wy = 12 + ri * 24
                    if wx + 8 <= bx + w - 4 and wy + 12 <= h - 6:
                        rect(wx, wy, wx + 8, wy + 12, rng.choice(LIT))
        # Neon edge down one side, and a bright line along the hanging base.
        edge = rng.choice(NEON)
        if rng.random() < 0.5:
            rect(bx, 0, bx + 2, h, edge)
        else:
            rect(bx + w - 2, 0, bx + w, h, edge)
        rect(bx, h - 3, bx + w, h, edge)
        # Half the towers end in a point aimed at the ground below.
        if rng.random() < 0.55:
            cx = bx + w // 2
            poly([(bx + 4, h), (bx + w - 4, h), (cx, h + 42)], body)
            disc(cx, h + 42, 3, edge)
        # Some towers dangle an antenna with a glowing tip.
        if rng.random() < 0.45:
            ax = bx + w // 2
            ln = rng.randrange(26, 56)
            rect(ax, h, ax + 2, h + ln, edge)
            disc(ax + 1, h + ln + 3, 4, (255, 240, 200))

    # Two sky-bridges strung between neighbouring towers, lights on.
    for k in range(0, len(towers) - 1, 3):
        x0, w0, h0, _ = towers[k]
        x1, w1, h1, _ = towers[k + 1]
        by = min(h0, h1) - 44
        if by > 60:
            rect(x0 + w0, by, x1, by + 3, (200, 220, 255))
            for lx in range(x0 + w0 + 8, x1 - 6, 16):
                disc(lx, by + 1, 2, (255, 196, 90))


# ---------------------------------------------------------------- the diving rocket

def paint_rocket():
    cx = 512
    # Warm halo behind the rocket so it pops off the violet sky.
    # Blended, not solid, so the glow fades instead of cutting a hard disc.
    ellipse_mix(cx, 540, 250, 210, (150, 70, 140), 0.30)
    ellipse_mix(cx, 540, 185, 155, (180, 90, 150), 0.30)
    ellipse_mix(cx, 540, 120, 100, (215, 110, 150), 0.30)

    # Flame ABOVE the rocket: it is diving, so the fire trails upward.
    ellipse(cx, 398, 54, 96, (255, 122, 26))
    ellipse(cx, 412, 37, 72, (255, 196, 60))
    ellipse(cx, 426, 21, 48, (255, 246, 200))

    # Rear nozzle at the top of the body.
    rect(487, 450, 537, 472, (40, 44, 66))

    # Fins, swept back toward the top because the rocket falls nose-first.
    poly([(457, 470), (398, 566), (457, 592)], (230, 70, 50))
    poly([(567, 470), (626, 566), (567, 592)], (230, 70, 50))
    poly([(457, 500), (424, 552), (457, 560)], (255, 150, 90))
    poly([(567, 500), (600, 552), (567, 560)], (255, 150, 90))

    # Body: bright white with a lit left edge and a shaded right edge.
    rect(457, 470, 567, 648, (238, 242, 248))
    rect(457, 470, 477, 648, (255, 255, 255))
    rect(537, 470, 567, 648, (168, 178, 200))
    # Orange band near the nose.
    rect(457, 600, 567, 628, (255, 110, 40))
    rect(457, 600, 567, 604, (255, 170, 80))

    # Nose cone, split light / shade, apex pointing straight down.
    poly([(457, 648), (512, 648), (512, 716)], (255, 140, 60))
    poly([(512, 648), (567, 648), (512, 716)], (214, 60, 30))
    disc(512, 716, 4, (255, 220, 120))

    # Round porthole window.
    disc(512, 545, 27, (30, 40, 70))
    disc(512, 545, 20, (90, 180, 235))
    disc(504, 537, 7, (255, 255, 255))

    # Speed streaks ripping past the rocket, vertical and long.
    streaks = [
        (388, 420, 200, 4, (255, 255, 255)),
        (414, 380, 260, 3, (210, 230, 255)),
        (442, 460, 150, 3, (255, 255, 255)),
        (582, 450, 170, 3, (255, 255, 255)),
        (612, 390, 240, 3, (210, 230, 255)),
        (640, 440, 180, 4, (255, 255, 255)),
        (360, 500, 120, 3, (180, 200, 255)),
        (668, 510, 110, 3, (180, 200, 255)),
    ]
    for sx, sy, ln, wd, col in streaks:
        rect(sx, sy, sx + wd, sy + ln, col)


def paint_skyfall():
    """Birds and debris FALLING UP, toward the city in the sky."""
    for _ in range(14):
        x = rng.randrange(60, W - 60)
        y = rng.randrange(700, 860)
        s = rng.randrange(10, 22)
        col = (22, 22, 48)
        poly([(x, y), (x - s, y - 7), (x - s + 5, y + 1)], col)
        poly([(x, y), (x + s, y - 7), (x + s - 5, y + 1)], col)
    for _ in range(24):
        x = rng.randrange(40, W - 40)
        y = rng.randrange(640, 900)
        col = rng.choice([(255, 220, 150), (200, 230, 255), (255, 255, 255)])
        rect(x, y, x + 4, y + 4, col)
        rect(x + 1, y + 5, x + 3, y + 18, (255, 255, 255))

    # One tiny astronaut tumbling upward, arms out, toward the city.
    ax, ay = 348, 612
    disc(ax, ay, 11, (240, 244, 250))
    disc(ax + 2, ay - 2, 6, (30, 50, 90))
    poly([(ax - 4, ay + 10), (ax + 10, ay + 10), (ax + 14, ay + 34), (ax - 8, ay + 34)],
         (255, 120, 50))
    poly([(ax - 4, ay + 12), (ax - 26, ay - 2), (ax - 22, ay + 4)], (255, 120, 50))
    poly([(ax + 10, ay + 12), (ax + 30, ay - 4), (ax + 26, ay + 4)], (255, 120, 50))
    rect(ax - 2, ay + 36, ax + 2, ay + 52, (255, 255, 255))


# ---------------------------------------------------------------- headline

# Hand-drawn 5x7 capitals, one row per string, '#' = ink.
FONT = {
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def paint_text(text, x0, y0, scale, col):
    x = x0
    for ch in text:
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    rect(
                        x + gx * scale,
                        y0 + gy * scale,
                        x + (gx + 1) * scale,
                        y0 + (gy + 1) * scale,
                        col,
                    )
        x += 6 * scale


def paint_headline():
    text = "DOWN IS UP!"
    scale = 12
    width = len(text) * 6 * scale - scale
    x0 = (W - width) // 2
    y0 = 878
    # Gold rule above, cyan rule below: the headline is framed, not floating.
    rect(x0, y0 - 16, x0 + width, y0 - 12, (255, 196, 90))
    rect(x0, y0 + 7 * scale + 12, x0 + width, y0 + 7 * scale + 16, (110, 230, 255))
    # Dark drop shadow first, then the bright face, so it reads on dawn sky.
    paint_text(text, x0 + 7, y0 + 9, scale, (12, 12, 48))
    paint_text(text, x0, y0, scale, (255, 243, 214))


# ---------------------------------------------------------------- main

def main():
    paint_sky()
    paint_stars()
    paint_clouds()
    paint_city()
    paint_rocket()
    paint_skyfall()
    paint_headline()
    save_png(rows)


if __name__ == "__main__":
    main()
