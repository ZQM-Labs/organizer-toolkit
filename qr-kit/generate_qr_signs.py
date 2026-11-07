#!/usr/bin/env python3
"""Generate printable QR signs for a ZQM Labs quest kit.

Usage: python3 generate_qr_signs.py <kit-config.json> [out.html]
Deps:  pip install segno   (BSD-licensed, pure Python)
Each stop sign's QR encodes the play URL with kit + stop code, so scanning
the sign is the checkpoint unlock in the quest player. The start poster QR
encodes the kit's access code (as ?ac=) for team registration; stop signs
use ?code= for the sign code — the player treats them as different params.
"""
import argparse, hashlib, html, os, sys, tempfile
from preflight import KIT_BYTES, PACK_BYTES, PreflightError, read_json, check_kit, check_pack_alignment, poster_url, stop_url, verify_url_shapes

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
        print(f"  warning: QR payload is version {qr.version} — shorten private identifiers if possible",
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

ART_MAX_BYTES = 8 * 1024 * 1024  # printable local images only

def art_html(path, root, outdir, alt=""):
    """Copy artwork without overwriting another sign's similarly named file.

    Asset filenames derive from the bytes, not the organizer path/basename.
    Existing matching content may be reused; mismatched or symlinked target
    files are rejected. Never copy art outside the source repository root.
    """
    if not path:
        return ""
    root = os.path.realpath(root)
    src = os.path.realpath(os.path.join(root, path))
    if os.path.commonpath((root, src)) != root:
        raise PreflightError("art path escapes repository root")
    if not os.path.isfile(src):
        print("  warning: configured artwork not found; skipping", file=sys.stderr)
        return ""
    with open(src, "rb") as handle:
        payload = handle.read(ART_MAX_BYTES + 1)
    if len(payload) > ART_MAX_BYTES:
        raise PreflightError("artwork exceeds 8 MiB printable asset limit")
    digest = hashlib.sha256(payload).hexdigest()
    ext = os.path.splitext(path)[1].lower()
    name = "asset-" + digest[:24] + ext
    art_dir = os.path.join(outdir, "art")
    if os.path.islink(art_dir):
        raise PreflightError("output art directory cannot be a symlink")
    os.makedirs(art_dir, exist_ok=True)
    dest = os.path.join(art_dir, name)
    try:
        with open(dest, "xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if os.path.islink(dest) or not os.path.isfile(dest):
            raise PreflightError("output artwork conflicts with an existing file")
        with open(dest, "rb") as handle:
            if hashlib.sha256(handle.read()).hexdigest() != digest:
                raise PreflightError("output artwork hash collision; refusing to overwrite")
    return f'<div class="art"><img src="art/{name}" alt="{tx(alt)}"></div>'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="Private QR sign kit configuration")
    parser.add_argument("output", nargs="?", default="out/signs.html")
    parser.add_argument("--pack", help="Six-stop quest pack; required to verify code/name alignment")
    parser.add_argument("--force", action="store_true", help="Explicitly overwrite a prior output")
    args = parser.parse_args()
    try:
        cfg = read_json(args.config, KIT_BYTES)
        check_kit(cfg)
        verify_url_shapes(cfg)
        if args.pack:
            check_pack_alignment(cfg, read_json(args.pack, PACK_BYTES))
    except (PreflightError, OSError) as exc:
        parser.error("Kit preflight failed: " + str(exc))
    if not args.pack:
        print("WARNING: sign kit has NOT been matched to the actual six-stop pack; "
              "do not distribute before pack validation and field tests", file=sys.stderr)
    out = args.output
    if os.path.islink(out):
        parser.error("output HTML must not be a symlink")
    if os.path.exists(out) and not args.force:
        parser.error("output already exists; choose a fresh name or use --force")
    for key in ("scare_default", "finale"):
        if key in cfg:
            print(f"Note: {key!r} is recorded in the config but not used by "
                  f"the sign generator or the player — it has no effect.",
                  file=sys.stderr)
    outdir = os.path.dirname(os.path.abspath(out)) or "."
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
    base = cfg["play_base_url"]
    signs = [SIGN.format(title=tx(cfg["game_title"]), heading=tx(cfg.get("start_heading", "Start Here!")),
        sub=f"{tx(cfg['community'])} · {tx(cfg['window'])}<br>Scan to join the hunt — one phone per team.",
        art=art_html(cfg.get("poster_art"), root, outdir, "Wisp leading the lantern parade"),
        qr=qr_svg(poster_url(cfg)),
        scan_hint=(f"Scan with your phone camera. Camera broken? Open "
                   f"<b>{tx(base)}</b> and enter the access code below."),
        foot=f"No app to install. Stuck? Your organizer has a hint line. Access code: {tx(cfg['access_code'])}")]
    for s in cfg["stops"]:
        signs.append(SIGN.format(title=tx(cfg["game_title"]),
            heading=tx(f"Stop {s['order']}: {s['name']}"),
            sub="You found a quest stop! Scan to unlock the puzzle.",
            art=art_html(s.get("art"), root, outdir, f"Art for {s['name']}"),
            qr=qr_svg(stop_url(cfg, s)),
            scan_hint=(f"Scan with your phone camera. Camera broken? Open "
                       f"<b>{tx(base)}</b> and enter the sign code below."),
            foot=tx(f"Sign code: {s['code']} · Place at: {s['placement']}")))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    unverified = (
        '<p role="note"><strong>NOT VALIDATED AGAINST A QUEST PACK.</strong> '
        'Match all six signs against the final pack and field-test before distribution.</p>'
        if not args.pack else ""
    )
    rendered = "<!DOCTYPE html><meta charset='utf-8'>" + CSS + unverified + "\n".join(signs)
    if args.force:
        # Stage the full HTML on the same filesystem before replacing it.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=outdir, prefix=".qr-stage-",
            suffix=".html", delete=False,
        ) as staged:
            temp_file = staged.name
            staged.write(rendered)
        try:
            os.replace(temp_file, out)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    else:
        # Exclusive creation remains fail-closed even if another process
        # created the output after the initial existence check.
        with open(out, "x", encoding="utf-8") as handle:
            handle.write(rendered)
    print(f"Wrote {out} — {len(signs)} signs (1 poster + {len(cfg['stops'])} stops).")

if __name__ == "__main__":
    main()
