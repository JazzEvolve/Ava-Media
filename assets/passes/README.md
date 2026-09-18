# VIP pass prop

A restricted-access VIP credential graphic for Ava Media posts and thumbnails.
Fictional prop art — the card carries a `PROP / NOT VALID FOR ENTRY` footer and
is not a credential for any real venue or event.

## Files

| File | What it is |
| --- | --- |
| `make_vip_pass.py` | Builds the credential SVG, barcode included. Stdlib only. |
| `render_png.py` | Rasterizes the SVG to an exact-size PNG via headless Chromium. |
| `vip-restricted.svg` | Rendered card, 720×1120, vector. |
| `vip-restricted.png` | Same card at 2×, 1440×2240. |

## Regenerating

```sh
python3 make_vip_pass.py --code AVA-VIP-R7-0042 --out vip-restricted.svg
python3 render_png.py --svg vip-restricted.svg --out vip-restricted.png
```

Anything on the card is overridable:

```sh
python3 make_vip_pass.py \
  --code AVA-VIP-R7-0099 \
  --holder "AVA" \
  --tier "A A A" \
  --zone "STAGE · GREEN ROOM" \
  --event "AVA MEDIA — NIGHT SERIES" \
  --out backstage.svg
```

`--module` sets the narrow-bar width in px (default 3); the symbol width scales
with it, and the script centres the symbol on the card either way.

## About the barcode

It is a genuine Code 128B symbol, encoded in `make_vip_pass.py` rather than
pulled from a barcode package, so there is nothing to install. Start code,
mod-103 check digit and stop pattern are all present, so a scanner reads back
exactly the `--code` string. Code 128B covers ASCII 32–126; anything outside
that range raises rather than silently mis-encoding.

The code itself is arbitrary — it decodes to a string and means nothing to any
real access-control system.

## Rendering note

`render_png.py` renders with 120px of vertical slack and crops back down.
Headless Chromium clips roughly the last 90 CSS px when the viewport height
equals the content height exactly, which silently cut the footer off earlier
renders.
