#!/usr/bin/env python3
"""Rasterize the pass SVG to an exact-size PNG using headless Chromium.

Headless Chromium clips the last ~90 CSS px when the viewport height equals
the content height, so we render with vertical padding and crop back down.
Cropping is done here with zlib so the script needs no imaging library.

    python3 render_png.py --svg vip-restricted.svg --out vip-restricted.png
"""

import argparse
import glob
import os
import struct
import subprocess
import sys
import tempfile
import zlib

PAD = 120  # CSS px of slack to dodge the headless viewport clip


def find_chrome():
    for pattern in (
        "/opt/pw-browsers/chromium*/chrome-linux/chrome",
        "/opt/pw-browsers/chromium*/chrome-linux/headless_shell",
        "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
    ):
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    sys.exit("no chromium binary found; the SVG is still the source of truth")


def decode_png(path):
    data = open(path, "rb").read()
    pos, idat, ihdr = 8, b"", None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    width, height, _, ctype = ihdr[0], ihdr[1], ihdr[2], ihdr[3]
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = width * channels
    rows, prev, cursor = [], bytearray(stride), 0
    for _ in range(height):
        filt = raw[cursor]
        line = bytearray(raw[cursor + 1:cursor + 1 + stride])
        cursor += 1 + stride
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            x = line[i]
            if filt == 1:
                x += a
            elif filt == 2:
                x += b
            elif filt == 3:
                x += (a + b) // 2
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                x += a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            line[i] = x & 0xFF
        rows.append(bytes(line))
        prev = line
    return width, height, channels, ctype, rows


def encode_png(path, width, channels, ctype, rows):
    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, len(rows), 8, ctype, 0, 0, 0)
    body = b"".join(b"\x00" + r[:width * channels] for r in rows)
    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", ihdr))
        handle.write(chunk(b"IDAT", zlib.compress(body, 9)))
        handle.write(chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", default="vip-restricted.svg")
    parser.add_argument("--out", default="vip-restricted.png")
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=1120)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    svg = os.path.abspath(args.svg)
    workdir = os.path.dirname(svg) or "."
    wrapper = os.path.join(workdir, ".render-wrapper.html")
    with open(wrapper, "w") as handle:
        handle.write(
            "<!doctype html><meta charset='utf-8'>"
            "<style>html,body{margin:0;padding:0;background:#07070a}"
            "img{display:block;width:%dpx;height:%dpx}</style>"
            "<img src='%s'>" % (args.width, args.height, os.path.basename(svg))
        )

    raw_png = os.path.join(tempfile.mkdtemp(), "raw.png")
    try:
        subprocess.run([
            find_chrome(), "--headless", "--disable-gpu", "--no-sandbox",
            "--hide-scrollbars",
            "--force-device-scale-factor=%d" % args.scale,
            "--window-size=%d,%d" % (args.width, args.height + PAD),
            "--screenshot=%s" % raw_png,
            "file://%s" % wrapper,
        ], check=True, capture_output=True)
    finally:
        os.remove(wrapper)

    width, _, channels, ctype, rows = decode_png(raw_png)
    keep = args.height * args.scale
    encode_png(args.out, args.width * args.scale, channels, ctype, rows[:keep])
    print("wrote %s (%dx%d)" % (args.out, args.width * args.scale, keep))


if __name__ == "__main__":
    main()
