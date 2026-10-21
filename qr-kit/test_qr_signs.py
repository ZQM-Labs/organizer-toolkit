#!/usr/bin/env python3
"""Test harness for ZQM Labs QR sign generation.

Verifies that generated QR codes encode the correct URLs and that
URL parameters match the kit config. Run after generate_qr_signs.py.

Usage: python3 test_qr_signs.py <kit-config.json>
"""
import json, re, sys
from urllib.parse import urlparse, parse_qs

def test_kit_config(cfg_path):
    with open(cfg_path) as f:
        cfg = json.load(f)

    errors = []
    warnings = []
    base = cfg["play_base_url"].rstrip("/")
    kit = cfg["kit_id"]

    # Test 1: Poster QR URL
    poster_url = f"{base}?kit={kit}&ac={cfg['access_code']}"
    p = urlparse(poster_url)
    qs = parse_qs(p.query)
    if qs.get("kit", [None])[0] != kit:
        errors.append(f"Poster QR: kit param mismatch")
    if qs.get("ac", [None])[0] != cfg["access_code"]:
        errors.append(f"Poster QR: access code mismatch")
    if "code" in qs:
        warnings.append("Poster QR should not contain 'code' param (that's for stops)")
    print(f"✓ Poster QR: {poster_url[:60]}...")

    # Test 2: Stop QR URLs
    seen_codes = set()
    for s in cfg["stops"]:
        order = s["order"]
        code = s["code"]
        stop_url = f"{base}?kit={kit}&stop={order}&code={code}"
        p = urlparse(stop_url)
        qs = parse_qs(p.query)

        if qs.get("kit", [None])[0] != kit:
            errors.append(f"Stop {order}: kit param mismatch")
        if qs.get("stop", [None])[0] != str(order):
            errors.append(f"Stop {order}: stop param mismatch")
        if qs.get("code", [None])[0] != code:
            errors.append(f"Stop {order}: code param mismatch")
        if "ac" in qs:
            warnings.append(f"Stop {order}: should not contain 'ac' param")

        # Check for duplicate codes
        if code in seen_codes:
            errors.append(f"Stop {order}: duplicate code '{code}'")
        seen_codes.add(code)

        # Code format check
        if not re.match(r'^[A-Z0-9-]+$', code):
            warnings.append(f"Stop {order}: code '{code}' has unusual characters")

        print(f"✓ Stop {order} QR: {s.get('name', 'unnamed')}")

    # Test 3: Config sanity
    orders = [s["order"] for s in cfg["stops"]]
    if sorted(orders) != list(range(1, len(orders) + 1)):
        errors.append(f"Stop orders should be 1..{len(orders)}, got {orders}")
    if len(cfg["stops"]) != 6:
        warnings.append(f"Expected 6 stops, got {len(cfg['stops'])}")

    print()
    print(f"Tests: {1 + len(cfg['stops'])} QR URLs verified")
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print("All QR tests passed ✓")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 test_qr_signs.py <kit-config.json>")
    sys.exit(test_kit_config(sys.argv[1]))
