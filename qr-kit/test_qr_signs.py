#!/usr/bin/env python3
"""Verify exact QR URL query shapes without printing private kit credentials.

  python qr-kit/test_qr_signs.py qr-kit/kit-config.example.json
  python qr-kit/test_qr_signs.py private-kit.json --pack private-pack.json

This checks the shared URL encoder and input relationships, not a camera
decoding printed physical QR symbols or server-side kit entitlements.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from preflight import (
    KIT_BYTES,
    PACK_BYTES,
    PreflightError,
    check_kit,
    check_pack_alignment,
    read_json,
    verify_url_shapes,
)


def check_kit_config(cfg_path, pack_path=None):
    """Return 0 only when all six QR query shapes and supplied data align."""
    try:
        cfg = read_json(cfg_path, KIT_BYTES)
        result = check_kit(cfg)
        verify_url_shapes(cfg)
        if pack_path is not None:
            result = check_pack_alignment(cfg, read_json(pack_path, PACK_BYTES))
    except (OSError, PreflightError) as exc:
        print("QR check FAILED: " + str(exc), file=sys.stderr)
        return 1
    print("QR URL preflight passed: 1 poster + 6 stops")
    if not result["pack_alignment_checked"]:
        print("WARNING: no quest pack supplied; codes and names NOT verified against playable pack")
    else:
        print("Six stop codes and names match supplied pack (full runtime validation still required)")
    return 0


def test_example_kit_config():
    """Bundled demo config must be structurally valid, not an activated paid kit."""
    cfg = Path(__file__).with_name("kit-config.example.json")
    assert check_kit_config(cfg) == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit")
    parser.add_argument("--pack")
    args = parser.parse_args()
    raise SystemExit(check_kit_config(args.kit, args.pack))
