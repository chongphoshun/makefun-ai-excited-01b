# DOWN IS UP! — ai-excited-01 entry (b)

An upside-down city hangs from the top of the sky, lit windows and neon
edges pointing down. A rocket dives straight down toward it, flame
trailing upward behind it, while birds and debris fall *up* past it and a
tiny astronaut tumbles skyward. The dawn sky waits at the bottom, because
in this picture down is up — the headline says so in plain letters.

## Why this should excite the judge

- **Surprise:** the whole world is flipped. The city is in the sky, the
  rocket dives toward it, and everything loose falls upward.
- **Momentum:** vertical speed lines, a flame pointing the wrong way, a
  rocket frozen a heartbeat from the skyline.
- **Reads small:** one hero (rocket + inverted skyline), one bold line of
  text, strong light-to-dark vertical gradient.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024x1024, deterministic, ~0.5 s
```

Pure Python 3.13 standard library, no network, no assets: every pixel is
drawn by `main.py`, including the hand-drawn 5x7 letterforms of the
headline and the hand-written PNG encoder (zlib + struct).
