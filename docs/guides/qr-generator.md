# QR Code Generator Guide

The QR sign generator lives in this repository, in
[`qr-kit/`](https://github.com/ZQM-Labs/organizer-toolkit/tree/main/qr-kit/) — no other repository access is needed. This guide
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

# 4. Generate signs
python3 generate_qr_signs.py my-kit.json signs.html

# 5. Test (verifies QR URLs match config)
python3 test_qr_signs.py my-kit.json

# 6. Print signs.html (one sign per page)
#    Use a browser's Print dialog, fit-to-page, color
```

Prefer a visual interface? Open `qr-kit/qr-manager.html` in a browser —
upload your kit config JSON to see all QR codes, test each URL, and run a
pre-print checklist. No server needed; it runs entirely in the browser.

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
| `window` | No | Displayed on the start poster |
| `stops` | Yes | Array of 6 stops (see below) |
| `finale` | No | `{location, treat}` for the finale table |

### Stop fields

| Field | Required | Description |
|---|---|---|
| `code` | Yes | Unique code (e.g. `LANTERN-1`) |
| `name` | Yes | Displayed on the sign |
| `order` | Yes | 1–6, sequential |
| `placement` | No | Where to put the sign |
| `art` | No | Path to art asset (relative to the repository root) |

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
