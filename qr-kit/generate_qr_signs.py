#!/usr/bin/env python3
"""Generate printable QR signs for a ZQM Labs quest kit.

Usage: python3 generate_qr_signs.py <kit-config.json> [out.html]
Deps:  pip install segno   (BSD-licensed, pure Python)
Each stop sign's QR encodes the play URL with kit + stop code, so scanning
the sign is the checkpoint unlock in the quest player. The start poster QR
encodes the kit's access code (as ?ac=) for team registration; stop signs
use ?code= for the sign code — the player treats them as different params.
"""
import html, io, json, os, shutil, sys
from urllib.parse import quote

try:
    import segno
except ImportError:
    sys.exit("Missing dependency: pip install segno")

def qr_svg(content, scale=10):
    """Return an inline SVG string for `content`.

    segno >= 1.0 exposes svg_inline(); the old QRCode.write() method was removed
    (it raised AttributeError on segno 1.6.x). svg_inline returns the markup
    directly, so no StringIO buffer is needed.

    Print-hardening for outdoor signs: error="h" recovers ~30% symbol damage
    (rain, smudges, sun fade, torn corners) vs ~15% at "m"; border=4 is the
    spec-minimum quiet zone — border=2 mis-scans at oblique angles.
    """
    qr = segno.make(content, error="h")
    if qr.version > 10:  # absurdly dense for a 4.2in print; payload likely wrong
        print(f"  warning: QR for {content[:40]!r}… is version {qr.version} — check payload length",
              file=sys.stderr)
    return qr.svg_inline(scale=scale, border=4)

SIGN = """<section class="sign">
  <div class="brand">🏮 Z'S QUESTS &amp; MISCHIEF · {title}</div>
  <h1>{heading}</h1><p class="sub">{sub}</p>
  {art}
  <div class="qr">{qr}</div><p class="scan-hint">{scan_hint}</p><p class="foot">{foot}</p>
</section>"""

CSS = """<style>
@page { size: Letter; margin: 0.5in; }
body { font-family: system-ui, sans-serif; text-align: center; color: #2b2118; }
.sign { page-break-after: always; padding-top: 0.6in; }
.brand { letter-spacing: 2px; font-size: 13px; }
h1 { font-size: 40px; margin: 12px 0 4px; } .sub { font-size: 19px; }
.art img { width: 2.4in; max-height: 2.4in; border-radius: 14px; margin: 6px 0; }
.qr svg { width: 4.2in; height: 4.2in; } .foot { font-size: 15px; margin-top: 10px; } .scan-hint { font-size: 16px; margin: 8px 0 0; }
</style>"""

def tx(s):
    """Escape organizer-supplied text for the sign HTML."""
    return html.escape(str(s))

def art_html(path, root, outdir, alt=""):
    """Copy an art file next to the signs and return its <img> block (or "")."""
    if not path:
        return ""
    src = os.path.join(root, path)
    if not os.path.isfile(src):
        print(f"  warning: art not found: {path} — skipping", file=sys.stderr)
        return ""
    art_dir = os.path.join(outdir, "art")
    os.makedirs(art_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(art_dir, os.path.basename(path)))
    return f'<div class="art"><img src="art/{os.path.basename(path)}" alt="{tx(alt)}"></div>' 

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 generate_qr_signs.py <kit-config.json> [out.html]")
    try:
        cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Kit config not found: {sys.argv[1]}")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in {sys.argv[1]}: {e}")
    for key in ("play_base_url", "kit_id", "game_title", "community",
                "window", "access_code", "stops"):
        if key not in cfg:
            sys.exit(f"Kit config missing required key: {key!r}")
    for i, st in enumerate(cfg["stops"]):
        if not isinstance(st, dict):
            sys.exit(f"Stop #{i} is not an object: {st!r}")
        for fkey in ("order", "name", "code", "placement"):
            if fkey not in st or st[fkey] in (None, ""):
                sys.exit(f"Stop #{i} missing required field {fkey!r} "
                         f"— each stop needs order, name, code, placement")
    orders = [st.get("order") for st in cfg["stops"]]
    if len(set(orders)) != len(orders):
        sys.exit(f"Duplicate stop order values in kit config: {orders}")
    for key in ("scare_default", "finale"):
        if key in cfg:
            print(f"Note: {key!r} is recorded in the config but not used by "
                  f"the sign generator or the player — it has no effect.",
                  file=sys.stderr)
    out = sys.argv[2] if len(sys.argv) > 2 else "out/signs.html"
    outdir = os.path.dirname(os.path.abspath(out)) or "."
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
    base, kit = cfg["play_base_url"], cfg["kit_id"]
    signs = [SIGN.format(title=tx(cfg["game_title"]), heading=tx(cfg.get("start_heading", "Start Here!")),
        sub=f"{tx(cfg['community'])} · {tx(cfg['window'])}<br>Scan to join the hunt — one phone per team.",
        art=art_html(cfg.get("poster_art"), root, outdir, "Wisp leading the lantern parade"),
        qr=qr_svg(f"{base}?kit={quote(kit)}&ac={quote(cfg['access_code'])}"),
        scan_hint=(f"Scan with your phone camera. Camera broken? Open "
                   f"<b>{tx(base)}</b> and enter the access code below."),
        foot=f"No app to install. Stuck? Your organizer has a hint line. Access code: {tx(cfg['access_code'])}")]
    for s in cfg["stops"]:
        signs.append(SIGN.format(title=tx(cfg["game_title"]),
            heading=tx(f"Stop {s['order']}: {s['name']}"),
            sub="You found a quest stop! Scan to unlock the puzzle.",
            art=art_html(s.get("art"), root, outdir, f"Art for {s['name']}"),
            qr=qr_svg(f"{base}?kit={quote(kit)}&stop={s['order']}&code={quote(s['code'])}"),
            scan_hint=(f"Scan with your phone camera. Camera broken? Open "
                       f"<b>{tx(base)}</b> and enter the sign code below."),
            foot=tx(f"Sign code: {s['code']} · Place at: {s['placement']}")))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write("<!DOCTYPE html><meta charset='utf-8'>" + CSS + "\n".join(signs))
    print(f"Wrote {out} — {len(signs)} signs (1 poster + {len(cfg['stops'])} stops).")

if __name__ == "__main__":
    main()
