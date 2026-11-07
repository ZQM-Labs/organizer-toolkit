# qr-kit — QR sign generator

Turns a game + a community into a printable, shippable **kit**. This is the
public home of the QR sign generator: organizers do **not** need access to
any private repository to use it.

## Generate a kit

```bash
pip install segno        # or: pip install -r requirements.txt
python3 generate_qr_signs.py kit-config.example.json   # -> out/signs.html (UNVERIFIED demo)
```

Print `out/signs.html` (one sign per page): the start poster carries the
access-code QR; each stop sign carries its checkpoint QR (which encodes the
play URL + stop code, so scanning *is* the unlock). Weatherproofing = zip
bags or sheet protectors — see the toolkit's
[print specs](../guides/print-specs.md).
QR codes print at error-correction level H (~30% damage recovery) with a full
4-module quiet zone for outdoor reliability, and every sign carries a
broken-camera fallback: type the play URL, enter the printed code.

## Pre-print release gate (new)

A **printable QR set is not proof that its codes match the actual six-stop quest pack**. Run the offline, standard-library preflight before printing:

```bash
python3 qr-kit/preflight.py qr-kit/kit-config.example.json
python3 qr-kit/preflight.py path/to/private-kit.json --pack path/to/private-quest-pack.json
python3 qr-kit/generate_qr_signs.py path/to/private-kit.json out/private-signs.html --pack path/to/private-quest-pack.json
python3 qr-kit/test_qr_signs.py path/to/private-kit.json --pack path/to/private-quest-pack.json
```

The bundled public example is **kit-only** and has `kit_id=DEMO`; it is not aligned with the separate public `SAMPLE` quest-pack JSON. Do not pair the two, advertise the example as a booked event, or publish an active access code.

Preflight rejects duplicate JSON fields, malformed source, non-HTTPS or parameter-bearing player URLs, missing/duplicate/invalid stop orders and codes, unsafe art paths, and (when `--pack` is supplied) mismatched pack kit ID, stop ID, stop name or stop code. It verifies **six matching sign entries**, not full SPEC v1 semantics, authorization, venue permissions, QR scan reliability or actual live player routing. Run the official [quest-authoring validator](https://github.com/ZQM-Labs/quest-authoring) and a field/device playtest separately.

The sign generator always runs kit preflight before writing. Without `--pack`, its output contains a prominent **UNVERIFIED** notice and the console warns that pack alignment was not checked. The generated HTML **intentionally contains the printed start/access code**, so keep the files private. Diagnostic output and the standalone preflight JSON report do not expose that code. The generator now refuses to overwrite an existing sign file unless you explicitly pass `--force`.

## Files

- `kit-config.example.json` — per-community config: names, codes, stop list,
  placement hints, finale spot. One config = one kit sold. Copy it and edit.
  Optional `art` / `poster_art` fields point at image files relative to the
  repository root; missing art is skipped with a warning.
- `generate_qr_signs.py` — Segno-based generator (stdlib + segno only)
- `preflight.py` — strict kit / optional pack compatibility gate with credential-free diagnostics
- `test_qr_signs.py` — URL-query checks: `python3 test_qr_signs.py kit-config.json --pack pack.json`
- `qr-manager.html` + `qr-manager-logic.js` — **local-only browser preview**: load a private kit, optionally load the matching six-stop pack, inspect safe link controls, then run the separate Python source preflight. Browser previews are **not** QR decode, link reachability, entitlement checks or full SPEC validation.
- `templates/` — sign & badge SVG masters (edit in Inkscape)

Full walkthrough: [`guides/qr-generator.md`](../guides/qr-generator.md) in
this repository.

**Browser security note:** The QR Manager never displays the start access-code value as page text, and copying or opening its link requires a deliberate click. It uses text-only DOM insertion and events rather than interpolated inline handlers. The original browser parser may silently accept duplicate JSON object keys, which is why the Python `preflight.py` remains mandatory before printing. The manager does not send or retain uploaded files or contacts; opening a test link **does** navigate to the supplied player server with that link's parameters.

## Consistency test between Python and browser previews

The offline Python preflight is the **authoritative** sign-generation gate. The browser preview is advisory, but its shared rules must not silently drift. Run the cross-language regression suite from the repository root with Python 3.12 and Node 22:

```bash
node --test qr-kit/qr-manager.test.cjs qr-kit/qr-python-parity.test.cjs
```

The parity tests submit the same 20 synthetic valid/invalid kit and pack cases to both implementations (including valid six-stop pairs, duplicate or missing stops, malformed tokens, mismatched pack data, insecure player URLs and incorrect Dial levels). They assert accept/reject results only, not secret values, live access, GPS accuracy, real-world booking, or server authorization.

The browser cannot detect duplicate JSON keys after `JSON.parse`, and it does not process sign artwork; those protections remain in the strict Python file preflight and sign generator. Passing shared structural fixtures is therefore **not** a reason to skip the authoritative Python preflight or field tests.

## Provenance & license

Originally developed as `lantern-kit` inside the private
`ZQM-Computing/zqm-labs` monorepo and published here on 2026-10-20 so public
organizers can generate signs without monorepo access. Same author, same
license as the rest of this repository: MIT (see `../LICENSE`). The only
changes made for publication were wording ("quest player" for the retired
monorepo player name) and removing example art paths that pointed at
monorepo-only assets.
