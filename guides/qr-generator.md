# QR Code Generator Guide

The QR sign generator lives in this repository, in
[`qr-kit/`](../qr-kit/) — no other repository access is needed. This guide
walks organizers through generating, testing, and printing QR signs for a
ZQM kit.

## Quick start

```bash
# 1. Install the one dependency
pip install segno

# 2. Go to the generator in this repo
cd qr-kit

# 3. Copy the example config and edit it
cp kit-config.example.json my-kit.json
# Edit my-kit.json: kit_id, access_code, community, stops, play_base_url

# 4. Check six stop codes/orders and the URL; do not output access codes
python3 preflight.py my-kit.json

# 5. For a real event, cross-check the final matching six-stop JSON pack
python3 preflight.py my-kit.json --pack path/to/private-pack.json

# 6. Only then generate and test private signs, using the same pack
python3 generate_qr_signs.py my-kit.json signs.html --pack path/to/private-pack.json
python3 test_qr_signs.py my-kit.json --pack path/to/private-pack.json

# 7. Print signs.html (one sign per page) and field-test all six scans
#    Keep signs.html and all access-code-bearing signs private
```

Prefer a visual interface? Open `qr-kit/qr-manager.html` from the
repository folder in a browser. Load the **kit config** and, optionally,
the **matching six-stop pack** to preview link controls and inspect structure.
It does not draw physical QR symbols, verify a live route, or certify
entitlements. Unlike the Python preflight, the browser JSON parser cannot
reliably reject duplicate object keys; complete the Python step above before
printing. Files are processed locally, but opening a test link sends the
encoded parameters to the selected server. The access code is hidden from
displayed text, not removed from the private link itself.

## Artwork and output integrity

If using optional `poster_art` or per-stop `art`, keep source files inside the cloned repository. The generator now writes content-addressed files in the output's `art/` folder, so two different `logo.png` files used on separate stops cannot silently replace one another. Source images larger than 8 MiB, existing tampered asset files and output symlink destinations are rejected. It does not silently overwrite a prior HTML file; `--force` explicitly replaces a regular HTML file using a staged write but never overwrites a mismatched art asset.

The generator first prepares all seven signs and optional images in a private staging directory. It then publishes complete assets and writes the complete private HTML file **last**. If publishing fails, newly added assets from that attempt are rolled back while earlier sign files remain unchanged. On supported POSIX filesystems, new HTML and art files are owner-only. Previously existing matching art keeps its prior permissions and must be reviewed separately.

Retain the generated `art/` assets beside the private `signs.html`, and check every picture and QR symbol in an actual browser and printed copy. These safeguards do not prove art rights, print quality, or field readiness.

**Consistent print order:** The six stops are always printed and previewed as **Stop 1 through Stop 6**, regardless of the order of the six objects in the JSON file. The generator does not change the source pack or stop IDs; the start poster remains first. Confirm physical placement and walking sequence independently before a real event.

## What you get

`signs.html` contains **7 pages**:

- **Page 1:** Start poster (access code QR for team registration)
- **Pages 2–7:** Stop signs (checkpoint QRs — scanning unlocks the stop)

Each sign includes:

- A QR code (error-correction H — survives ~30% damage)
- The stop name and code (human-readable fallback)
- Placement hint from the config
- Broken-camera fallback: type the play URL + code manually

## Config reference

| Field | Required | Description |
|---|---|---|
| `kit_id` | Yes | Short unique ID (e.g. `DEMO`, `RIVERFEST-2026`) |
| `access_code` | Yes | Teams enter this at the start poster |
| `community` | Yes | Displayed on the start poster |
| `game_title` | Yes | Displayed on all signs |
| `play_base_url` | Yes | The deployed quest player URL |
| `scare_default` | No | `cozy` (default), `spooky`, `afterdark`, `overdrive` |
| `window` | Yes | Displayed on the start poster |
| `stops` | Yes | Array of 6 stops (see below) |
| `finale` | No | `{location, treat}` for the finale table |

### Stop fields

| Field | Required | Description |
|---|---|---|
| `code` | Yes | Unique code (e.g. `LANTERN-1`) |
| `name` | Yes | Displayed on the sign |
| `order` | Yes | 1–6, sequential |
| `placement` | Yes | Where to put the sign |
| `art` | No | Path to art asset (relative to the repository root) |

## Before distributing signs

The CLI preflight rejects malformed or duplicate-key JSON, insecure or pre-parameterized player URLs, bad or repeated six-stop codes, invalid orders, and unsafe art paths. With `--pack`, it additionally checks the pack's `kit` identifier and every stop's ID, name and code against the sign config. This is a **structural compatibility check**, not full content validation or proof that an event is available. Run the separate [quest-authoring validator](https://github.com/ZQM-Labs/quest-authoring), confirm the deployed player and entitlement state, and field-test the actual route.

Without `--pack`, the sign generator intentionally marks the printed set **NOT VALIDATED AGAINST A QUEST PACK**. A previous output file will not be silently overwritten; `--force` is required to replace it. Never upload sign HTML, access codes, private pack answers or participant details to public GitHub. Console verification prints field names and safe status messages, **not credential-bearing URLs**.

## QR URL scheme

- **Poster QR:** `?kit=<kit_id>&ac=<access_code>` — team registration
- **Stop QR:** `?kit=<kit_id>&stop=<order>&code=<code>` — checkpoint unlock

The quest player treats `ac` and `code` as different params. Don't mix them up.

## Printing & placement tips

- **Paper:** 24 lb+ bright white (standard copy paper works but curls)
- **Ink:** Color, high quality
- **Weatherproofing:** Zip bags or sheet protectors (Florida dew is real)
- **Placement:** Eye height for kids (3–4 ft), facing the path, secure from wind
- **Shade is the scan killer:** a sign under tree canopy in dappled or
  shaded light scans noticeably slower (learned in the 2026-10-14 playtest,
  where the Stop 4 sign took ~4 s under a tree). Mount signs at about
  **5.5 ft** or shift them a couple of feet out of canopy shade into even
  light with good sun exposure.
- **Test in event light:** scan every sign with your phone at the same time
  of day you'll run the event — morning shade and afternoon shade are
  different signs.

Full print specs: [print-specs.md](print-specs.md).

## Troubleshooting

| Problem | Fix |
|---|---|
| QR won't scan | Check error-correction (should be H), increase sign size, move the sign out of canopy shade |
| Wrong stop loads | Verify `code` field matches between config and sign |
| `segno` not found | `pip install segno` (not `pip install qrcode`) |
| Art not showing | Check `art` path is relative to the repository root, file exists |
| Too many/few pages | Config should have exactly 6 stops |
