# qr-kit — QR sign generator

Turns a game + a community into a printable, shippable **kit**. This is the
public home of the QR sign generator: organizers do **not** need access to
any private repository to use it.

## Generate a kit

```bash
pip install segno        # or: pip install -r requirements.txt
python3 generate_qr_signs.py kit-config.example.json   # -> out/signs.html
```

Print `out/signs.html` (one sign per page): the start poster carries the
access-code QR; each stop sign carries its checkpoint QR (which encodes the
play URL + stop code, so scanning *is* the unlock). Weatherproofing = zip
bags or sheet protectors — see the toolkit's
[print specs](../guides/print-specs.md).
QR codes print at error-correction level H (~30% damage recovery) with a full
4-module quiet zone for outdoor reliability, and every sign carries a
broken-camera fallback: type the play URL, enter the printed code.

## Files

- `kit-config.example.json` — per-community config: names, codes, stop list,
  placement hints, finale spot. One config = one kit sold. Copy it and edit.
  Optional `art` / `poster_art` fields point at image files relative to the
  repository root; missing art is skipped with a warning.
- `generate_qr_signs.py` — Segno-based generator (stdlib + segno only)
- `test_qr_signs.py` — QR URL verification: `python3 test_qr_signs.py kit-config.json`
- `qr-manager.html` — organizer QR management in the browser (upload config,
  test links, pre-print checklist). No server needed.
- `templates/` — sign & badge SVG masters (edit in Inkscape)

Full walkthrough: [`guides/qr-generator.md`](../guides/qr-generator.md) in
this repository.

## Provenance & license

Originally developed as `lantern-kit` inside the private
`ZQM-Computing/zqm-labs` monorepo and published here on 2026-10-20 so public
organizers can generate signs without monorepo access. Same author, same
license as the rest of this repository: MIT (see `../LICENSE`). The only
changes made for publication were wording ("quest player" for the retired
monorepo player name) and removing example art paths that pointed at
monorepo-only assets.
