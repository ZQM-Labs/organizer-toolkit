#!/usr/bin/env python3
"""Fail-closed, credential-safe QR kit and optional quest-pack alignment preflight.

  python qr-kit/preflight.py qr-kit/kit-config.example.json
  python qr-kit/preflight.py my-private-kit.json --pack my-private-pack.json

No network calls or code/answer values in CLI output. Structural alignment
does NOT validate the full SPEC v1, venue rights, player entitlements,
production routing, or real-world field readiness.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlencode, urlsplit

KIT_BYTES = 65_536
PACK_BYTES = 4 * 1024 * 1024
CODE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
KNOWN_ART_EXTS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".svg"})
REQUIRED = frozenset({
    "access_code", "community", "game_title", "kit_id",
    "play_base_url", "window", "stops",
})


class PreflightError(ValueError):
    """Invalid or incompatible organizer inputs, never containing code values."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PreflightError("duplicate JSON object key")
        result[key] = value
    return result


def _nonfinite(_value):
    raise PreflightError("non-standard NaN or Infinity JSON constant")


def read_json(path: str | Path, max_bytes: int) -> dict:
    """Bounded, strict UTF-8 JSON, including duplicate-key rejection."""
    source = Path(path)
    with source.open("rb") as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise PreflightError("input JSON exceeds bounded size")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise PreflightError("malformed or non-UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise PreflightError("input must be a JSON object")
    return value


def _printable_text(value, name, limit=150):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise PreflightError(name + " must be nonempty printable text")
    return value


def _credential(value, name):
    if not isinstance(value, str) or not CODE.fullmatch(value):
        raise PreflightError(name + " must be 3–64 uppercase letters, digits or hyphens")
    return value


def _base_url(value):
    _printable_text(value, "play_base_url", 512)
    if any(c.isspace() for c in value):
        raise PreflightError("play_base_url cannot contain whitespace")
    try:
        url = urlsplit(value)
        host = url.hostname
        port = url.port
    except ValueError as exc:
        raise PreflightError("play_base_url is malformed") from exc
    if (url.scheme != "https" or not host or url.username or url.password
            or url.query or url.fragment or not url.path.endswith("/")):
        raise PreflightError(
            "play_base_url must be an HTTPS path ending in /, without credentials, query or fragment"
        )
    if port is not None and not (1 <= port <= 65535):
        raise PreflightError("invalid play_base_url port")
    return value


def _safe_art(value, name):
    if value is None:
        return
    _printable_text(value, name, 250)
    # Normalize separator policy across Linux/Windows; a path in a config
    # may be copied into the HTML output, never interpreted as an URL.
    if "\\" in value or ":" in value:
        raise PreflightError(name + " must be a relative local asset path")
    path = PurePosixPath(value)
    if (path.is_absolute() or ".." in path.parts or "." in path.parts
            or path.suffix.lower() not in KNOWN_ART_EXTS):
        raise PreflightError(name + " must be a safe relative image path")


def check_kit(cfg: dict) -> dict:
    """Validate structural invariants used by the QR sign generator."""
    if not isinstance(cfg, dict) or not REQUIRED.issubset(cfg):
        raise PreflightError("kit config is missing required organizer fields")
    base = _base_url(cfg["play_base_url"])
    _credential(cfg["kit_id"], "kit_id")
    _credential(cfg["access_code"], "access_code")
    for field in ("community", "game_title", "window"):
        _printable_text(cfg[field], field)
    if "start_heading" in cfg:
        _printable_text(cfg["start_heading"], "start_heading")
    if "scare_default" in cfg and cfg["scare_default"] not in (
        "cozy", "spooky", "afterdark", "overdrive"
    ):
        raise PreflightError("scare_default is not a known Dial level")
    _safe_art(cfg.get("poster_art"), "poster_art")
    stops = cfg["stops"]
    if not isinstance(stops, list) or len(stops) != 6:
        raise PreflightError("kit requires exactly six stop-sign objects")
    orders, codes = set(), set()
    for index, item in enumerate(stops, 1):
        if not isinstance(item, dict):
            raise PreflightError(f"stop position {index} must be an object")
        order = item.get("order")
        if type(order) is not int or not 1 <= order <= 6:
            raise PreflightError(f"stop position {index} requires integer order from 1 to 6")
        if order in orders:
            raise PreflightError("duplicate stop order")
        orders.add(order)
        code = _credential(item.get("code"), f"stop {order} code")
        if code in codes or code == cfg["access_code"]:
            raise PreflightError("stop code must be unique and distinct from access code")
        codes.add(code)
        _printable_text(item.get("name"), f"stop {order} name")
        _printable_text(item.get("placement"), f"stop {order} placement", 250)
        _safe_art(item.get("art"), f"stop {order} art")
    if orders != set(range(1, 7)):
        raise PreflightError("stop orders must be 1 through 6")
    return {
        "status": "kit_structure_valid",
        "kit_stop_count": 6,
        "pack_alignment_checked": False,
        "field_or_entitlement_verified": False,
    }


def check_pack_alignment(cfg: dict, pack: dict) -> dict:
    """Require exact id/name/code parity; do NOT claim full player validation."""
    result = check_kit(cfg)
    if not isinstance(pack, dict) or pack.get("kit") != cfg["kit_id"]:
        raise PreflightError("quest pack kit identifier does not match sign kit")
    stops = pack.get("stops")
    if not isinstance(stops, list) or len(stops) != 6:
        raise PreflightError("quest pack requires exactly six stops")
    packed = {}
    for index, item in enumerate(stops, 1):
        if not isinstance(item, dict) or type(item.get("id")) is not int:
            raise PreflightError(f"quest pack stop {index} has invalid ID")
        sid = item["id"]
        if sid < 1 or sid > 6 or sid in packed:
            raise PreflightError("quest pack stop IDs must be unique 1 through 6")
        packed[sid] = item
    for sign in cfg["stops"]:
        order = sign["order"]
        item = packed.get(order)
        if item is None or item.get("code") != sign["code"]:
            raise PreflightError(f"stop {order}: QR sign code does not match quest pack")
        if item.get("name") != sign["name"]:
            raise PreflightError(f"stop {order}: QR sign name does not match quest pack")
    result.update(status="kit_pack_aligned", pack_alignment_checked=True)
    return result


def poster_url(cfg):
    """Same encoder used by poster generation and verification."""
    return cfg["play_base_url"] + "?" + urlencode(
        {"kit": cfg["kit_id"], "ac": cfg["access_code"]}
    )


def stop_url(cfg, item):
    """Same encoder used by stop generation and verification."""
    return cfg["play_base_url"] + "?" + urlencode(
        {"kit": cfg["kit_id"], "stop": item["order"], "code": item["code"]}
    )


def verify_url_shapes(cfg):
    """Inspect actual URLs without printing or copying credential values."""
    poster = parse_qs(urlsplit(poster_url(cfg)).query, strict_parsing=True)
    if poster != {"kit": [cfg["kit_id"]], "ac": [cfg["access_code"]]}:
        raise PreflightError("poster URL query parameters do not match configuration")
    for item in cfg["stops"]:
        fields = parse_qs(urlsplit(stop_url(cfg, item)).query, strict_parsing=True)
        if fields != {"kit": [cfg["kit_id"]], "stop": [str(item["order"])], "code": [item["code"]]}:
            raise PreflightError(f"stop {item['order']}: encoded QR parameters mismatch")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", type=Path, help="Private kit configuration JSON")
    parser.add_argument("--pack", type=Path, help="Matching six-stop quest pack JSON")
    parser.add_argument("--json", action="store_true", help="Emit safe summary; never codes or URLs")
    args = parser.parse_args(argv)
    try:
        cfg = read_json(args.kit, KIT_BYTES)
        result = check_kit(cfg)
        verify_url_shapes(cfg)
        if args.pack:
            pack = read_json(args.pack, PACK_BYTES)
            result = check_pack_alignment(cfg, pack)
    except (OSError, PreflightError) as exc:
        # Never print source values: exceptions in read/check contain keys,
        # field names or fixed messages only.
        print("Preflight FAILED: " + str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("Preflight PASSED: " + result["status"])
        if not result["pack_alignment_checked"]:
            print("WARNING: no quest pack supplied; codes and names NOT cross-checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
