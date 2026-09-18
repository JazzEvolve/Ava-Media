#!/usr/bin/env python3
"""Render a VIP 'restricted access' credential as SVG, barcode included.

Pure stdlib: the Code 128B symbol is encoded here rather than pulled from a
barcode package, so the script runs anywhere python3 does.

    python3 make_vip_pass.py --code AVA-VIP-R7-0042 --out vip-restricted.svg
"""

import argparse
import html

# Code 128 patterns, values 0-106. Each digit is a module width, bars and
# spaces alternating, starting with a bar. Value 106 is the stop pattern.
PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312",
    "132212", "221213", "221312", "231212", "112232", "122132", "122231", "113222",
    "123122", "123221", "223211", "221132", "221231", "213212", "223112", "312131",
    "311222", "321122", "321221", "312212", "322112", "322211", "212123", "212321",
    "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121",
    "313121", "211331", "231131", "213113", "213311", "213131", "311123", "311321",
    "331121", "312113", "312311", "332111", "314111", "221411", "431111", "111224",
    "111422", "121124", "121421", "141122", "141221", "112214", "112412", "122114",
    "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112",
    "421211", "212141", "214121", "412121", "111143", "111341", "131141", "114113",
    "114311", "411113", "411311", "113141", "114131", "311141", "411131", "211412",
    "211214", "211232", "2331112",
]

START_B = 104
STOP = 106


def code128b_values(text):
    """Start code, payload, mod-103 check digit, stop."""
    for ch in text:
        if not 32 <= ord(ch) <= 126:
            raise ValueError("Code 128B covers ASCII 32-126 only: %r" % ch)
    payload = [ord(ch) - 32 for ch in text]
    checksum = START_B
    for position, value in enumerate(payload, start=1):
        checksum += position * value
    return [START_B] + payload + [checksum % 103, STOP]


def barcode_bars(text, module=3, height=150, x=0, y=0):
    """Return (svg_rects, total_width). Bars only: quiet zones are the caller's."""
    rects = []
    cursor = x
    for value in code128b_values(text):
        is_bar = True
        for width_digit in PATTERNS[value]:
            width = int(width_digit) * module
            if is_bar:
                rects.append(
                    '<rect x="%g" y="%g" width="%g" height="%g" fill="#0b0b0f"/>'
                    % (cursor, y, width, height)
                )
            cursor += width
            is_bar = not is_bar
    return rects, cursor - x


def build_pass(code, holder, tier, zone, event, issuer, module=3):
    width, height = 720, 1120
    bar_h = 150
    bars, bar_w = barcode_bars(code, module=module, height=bar_h, x=0, y=0)
    bar_x = (width - bar_w) / 2.0
    esc = html.escape

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}" role="img"
     aria-label="{esc(tier)} credential for {esc(holder)}, barcode {esc(code)}">
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#15151d"/>
      <stop offset="55%" stop-color="#0d0d13"/>
      <stop offset="100%" stop-color="#17121a"/>
    </linearGradient>
    <linearGradient id="foil" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#e8c87a"/>
      <stop offset="45%" stop-color="#fdf3d0"/>
      <stop offset="100%" stop-color="#c49a48"/>
    </linearGradient>
    <linearGradient id="hazard" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#b8123a"/>
      <stop offset="100%" stop-color="#7d0a26"/>
    </linearGradient>
    <clipPath id="cardClip"><rect x="24" y="24" width="672" height="1072" rx="34"/></clipPath>
  </defs>

  <rect width="{width}" height="{height}" fill="#07070a"/>
  <rect x="24" y="24" width="672" height="1072" rx="34" fill="url(#card)"
        stroke="url(#foil)" stroke-width="2"/>

  <g clip-path="url(#cardClip)" opacity="0.5">
    <g stroke="#ffffff" stroke-opacity="0.045" stroke-width="1">
      {"".join(f'<line x1="24" y1="{ypos}" x2="696" y2="{ypos}"/>' for ypos in range(60, 1100, 14))}
    </g>
  </g>

  <!-- lanyard slot -->
  <rect x="300" y="62" width="120" height="20" rx="10" fill="#07070a"
        stroke="#3a3a46" stroke-width="1.5"/>

  <!-- issuer -->
  <text x="360" y="150" text-anchor="middle" fill="url(#foil)"
        font-family="Georgia, 'DejaVu Serif', serif" font-size="30"
        letter-spacing="10">{esc(issuer)}</text>
  <text x="360" y="178" text-anchor="middle" fill="#8a8a99"
        font-family="'Helvetica Neue', Arial, sans-serif" font-size="13"
        letter-spacing="5">CREDENTIAL — NON-TRANSFERABLE</text>

  <!-- tier -->
  <rect x="120" y="212" width="480" height="104" rx="8" fill="url(#foil)"/>
  <text x="360" y="284" text-anchor="middle" fill="#0b0b0f"
        font-family="Impact, 'DejaVu Sans', sans-serif" font-size="66"
        letter-spacing="14">{esc(tier)}</text>

  <!-- restricted band -->
  <rect x="88" y="336" width="544" height="58" rx="6" fill="url(#hazard)"/>
  <text x="360" y="374" text-anchor="middle" fill="#fff6f8"
        font-family="'Helvetica Neue', Arial, sans-serif" font-size="25"
        font-weight="bold" letter-spacing="7">RESTRICTED ACCESS</text>

  <!-- holder / event block -->
  <g font-family="'Helvetica Neue', Arial, sans-serif">
    <text x="88" y="458" fill="#7c7c8c" font-size="13" letter-spacing="4">HOLDER</text>
    <text x="88" y="496" fill="#f2f2f6" font-size="34">{esc(holder)}</text>

    <text x="88" y="556" fill="#7c7c8c" font-size="13" letter-spacing="4">ENGAGEMENT</text>
    <text x="88" y="590" fill="#dcdce4" font-size="23">{esc(event)}</text>

    <text x="88" y="648" fill="#7c7c8c" font-size="13" letter-spacing="4">ZONES</text>
    <text x="88" y="682" fill="#dcdce4" font-size="23">{esc(zone)}</text>
  </g>

  <line x1="88" y1="726" x2="632" y2="726" stroke="#2c2c38" stroke-width="1"/>
  <text x="88" y="762" fill="#6d6d7d"
        font-family="'Helvetica Neue', Arial, sans-serif" font-size="13">
    Escort required beyond marked zones. Present on request.
  </text>

  <!-- barcode, on its own white quiet-zone panel -->
  <rect x="64" y="808" width="592" height="230" rx="10" fill="#ffffff"/>
  <g transform="translate({bar_x:.2f}, 838)">
    {"".join(bars)}
  </g>
  <text x="360" y="1014" text-anchor="middle" fill="#0b0b0f"
        font-family="'Courier New', 'DejaVu Sans Mono', monospace" font-size="27"
        letter-spacing="4">{esc(code)}</text>

  <text x="360" y="1072" text-anchor="middle" fill="#55556a"
        font-family="'Helvetica Neue', Arial, sans-serif" font-size="12"
        letter-spacing="3">PROP / NOT VALID FOR ENTRY</text>
</svg>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", default="AVA-VIP-R7-0042")
    parser.add_argument("--holder", default="AVA")
    parser.add_argument("--tier", default="V I P")
    parser.add_argument("--zone", default="STAGE · GREEN ROOM · PRESS PIT")
    parser.add_argument("--event", default="AVA MEDIA — NIGHT SERIES")
    parser.add_argument("--issuer", default="AVA MEDIA")
    parser.add_argument("--module", type=int, default=3, help="narrow-bar width in px")
    parser.add_argument("--out", default="vip-restricted.svg")
    args = parser.parse_args()

    svg = build_pass(
        args.code, args.holder, args.tier, args.zone,
        args.event, args.issuer, module=args.module,
    )
    with open(args.out, "w") as handle:
        handle.write(svg)
    print("wrote %s (%s)" % (args.out, args.code))


if __name__ == "__main__":
    main()
