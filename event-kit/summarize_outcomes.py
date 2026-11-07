#!/usr/bin/env python3
"""Calculate privacy-suppressed, host-entered aggregate quest outcomes offline.

This tool never fetches analytics or participants. It cannot verify a sale,
completion, share, transaction, event, or the truth of user-entered counts.
Usage: python event-kit/summarize_outcomes.py event-kit/examples/outcomes.synthetic.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA_VERSION = 1
MIN_DENOMINATOR = 10
MIN_CELL = 5
COUNT_KEYS = {
    "teams_invited", "teams_started", "teams_completed",
    "teams_sharing_offered", "teams_shared_reported",
    "teams_with_timing", "total_completion_minutes",
    "qualified_host_inquiries", "proposals_sent", "pilots_accepted",
}
FIELDS = {"schema_version", "source_basis", *COUNT_KEYS}
SOURCES = {"synthetic_demo", "manual_host_aggregate"}
LIMIT = 1_000_000


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON field: " + key)
        obj[key] = value
    return obj


def load(path: Path):
    if path.stat().st_size > 16_384:
        raise ValueError("Input exceeds 16 KiB: never load raw event logs")
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON is forbidden")),
    )


def _rate(numerator, denominator):
    # Complementary cell suppression prevents an exposed percentage from
    # revealing a near-unique success or failure in a small cohort.
    if denominator < MIN_DENOMINATOR or numerator < MIN_CELL or denominator - numerator < MIN_CELL:
        return {"status": "suppressed", "value": None}
    return {"status": "reportable_aggregate", "value": round(100 * numerator / denominator, 1)}


def _average(total_minutes, observed_teams):
    if observed_teams < MIN_DENOMINATOR:
        return {"status": "suppressed", "value": None}
    return {"status": "reportable_aggregate", "value": round(total_minutes / observed_teams, 1)}


def calculate(raw):
    if not isinstance(raw, dict) or set(raw) != FIELDS:
        raise ValueError("Input must contain only the documented aggregate fields")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported schema_version")
    if not isinstance(raw["source_basis"], str) or raw["source_basis"] not in SOURCES:
        raise ValueError("Invalid source_basis")
    for key in COUNT_KEYS:
        val = raw[key]
        if type(val) is not int or not 0 <= val <= LIMIT:
            raise ValueError(key + " must be a non-negative bounded integer")
    constraints = (
        ("teams_started", "teams_invited"),
        ("teams_completed", "teams_started"),
        ("teams_sharing_offered", "teams_completed"),
        ("teams_shared_reported", "teams_sharing_offered"),
        ("teams_with_timing", "teams_completed"),
        ("proposals_sent", "qualified_host_inquiries"),
        ("pilots_accepted", "proposals_sent"),
    )
    for small, large in constraints:
        if raw[small] > raw[large]:
            raise ValueError(small + " cannot exceed " + large)
    timed = raw["teams_with_timing"]
    minutes = raw["total_completion_minutes"]
    if (timed == 0 and minutes != 0) or (timed > 0 and not timed <= minutes <= timed * 480):
        raise ValueError("total_completion_minutes must reflect 1–480 minutes per timed team")

    metrics = {
        "team_start_rate_percent": _rate(raw["teams_started"], raw["teams_invited"]),
        "team_completion_rate_percent": _rate(raw["teams_completed"], raw["teams_started"]),
        "voluntary_share_rate_percent": _rate(raw["teams_shared_reported"], raw["teams_sharing_offered"]),
        "mean_completion_minutes": _average(minutes, timed),
        "host_proposal_rate_percent": _rate(raw["proposals_sent"], raw["qualified_host_inquiries"]),
        "pilot_acceptance_rate_percent": _rate(raw["pilots_accepted"], raw["proposals_sent"]),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "basis": raw["source_basis"],
        "source_verified": False,
        "publishable_sales_proof": False,
        "analytics_automatically_collected": False,
        "metrics": metrics,
        "limitations": [
            "Host-entered aggregates are not validated transactions or an independently audited event.",
            "All rate denominators are explicit in the accompanying documentation.",
            "Rates with small or near-unique cohorts are suppressed; missing data is not zero.",
            "Do not publish synthetic fixture outputs as ZQM performance or sales.",
            "A completed quest, shared score, inquiry, proposal or accepted pilot is not proof of payment.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Local aggregate-only JSON; never raw participant logs")
    args = parser.parse_args()
    try:
        result = calculate(load(args.input))
    except (OSError, ValueError, UnicodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
