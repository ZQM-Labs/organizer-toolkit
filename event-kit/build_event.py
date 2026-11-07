#!/usr/bin/env python3
"""Build a static, offline host planning kit; never schedule a live game or collect GPS.

python event-kit/build_event.py event-kit/examples/community-day.json --output out/event
Python 3.11+ with system IANA timezone data (no Python package dependency).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SCHEMA = 1
FIELDS = {
    "schema_version", "event_id", "event_title", "theme", "timezone",
    "start_local", "duration_minutes", "team_slots", "stagger_minutes",
    "finale_minutes", "venue_label", "surprise_enabled",
}
THEMES = {
    "community": "Neighborhood story and cooperation",
    "heritage": "Public history and place-based learning",
    "school": "Supervised outdoor field learning",
    "team": "Shared puzzles and team-building",
    "seasonal": "Seasonal story and group discovery",
}
PROMPTS = (
    "Notice a safe public detail that represents today's theme. Describe or sketch it.",
    "Choose a shape or pattern at an approved stop. Explain what catches your attention.",
    "Spot a public, non-sensitive sign of change or care for the environment.",
    "Find a color or texture you can describe without identifying a person or home.",
    "Share an original one-sentence story inspired by a permitted public feature.",
    "Celebrate your team with a verbal recap or drawing; photo participation is optional.",
)
BONUSES = (
    "Optional surprise: invent a five-word title for your team's story.",
    "Optional surprise: sketch a symbol for today's theme.",
    "Optional surprise: thank a teammate for a thoughtful observation.",
    "Optional surprise: describe one accessible way to enjoy the story.",
)
ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,47}$")
WALL = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
NOTICE = (
    "PLANNING EXAMPLE ONLY. Not a released route, booking, real-time event,"
    " GPS tracker, participant leaderboard, live join service, or approved venue."
)
PRIVACY = (
    "Sharing is optional. Obtain consent before recording or publishing. "
    "Do not photograph strangers or homes, include precise GPS/EXIF metadata, "
    "or upload participant locations. Offer a written or sketched alternative."
)


def _json_object(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("Duplicate JSON field: " + key)
        data[key] = value
    return data


def load_config(path: Path) -> dict:
    if path.stat().st_size > 16_384:
        raise ValueError("Event configuration exceeds 16 KiB")
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_json_object,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON forbidden")),
    )


def _text(value, name, limit=100):
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(ch) < 32 for ch in value)):
        raise ValueError(name + " must be short, printable, nonempty text")
    return value.strip()


def _integer(cfg, name, lo, hi):
    value = cfg[name]
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer from {lo} to {hi}")
    return value


def _local_time(value, zone):
    if not isinstance(value, str) or not WALL.fullmatch(value):
        raise ValueError("start_local must use YYYY-MM-DDTHH:MM (no offset)")
    try:
        naive = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid start_local calendar date/time") from exc
    # Reject DST gaps and ambiguous repeated clock hours rather than silently
    # scheduling a host gathering at the wrong instant.
    candidates = set()
    for fold in (0, 1):
        local = naive.replace(tzinfo=zone, fold=fold)
        instant = local.astimezone(timezone.utc)
        if instant.astimezone(zone).replace(tzinfo=None) == naive:
            candidates.add(instant)
    if len(candidates) != 1:
        raise ValueError("start_local is ambiguous or nonexistent in this timezone")
    return candidates.pop().astimezone(zone)


def compile_event(cfg: dict) -> dict:
    if not isinstance(cfg, dict) or set(cfg) != FIELDS:
        raise ValueError("Config must have exactly these fields: " + ", ".join(sorted(FIELDS)))
    if type(cfg["schema_version"]) is not int or cfg["schema_version"] != SCHEMA:
        raise ValueError("Unsupported schema_version")
    event_id = cfg["event_id"]
    if not isinstance(event_id, str) or not ID.fullmatch(event_id):
        raise ValueError("event_id must be a short lowercase slug")
    title = _text(cfg["event_title"], "event_title")
    venue = _text(cfg["venue_label"], "venue_label", 140)
    theme = cfg["theme"]
    if theme not in THEMES:
        raise ValueError("Unsupported theme")
    zone_name = _text(cfg["timezone"], "timezone", 64)
    try:
        zone = ZoneInfo(zone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Unknown IANA timezone") from exc
    start = _local_time(cfg["start_local"], zone)
    duration = _integer(cfg, "duration_minutes", 60, 480)
    team_slots = _integer(cfg, "team_slots", 1, 20)
    stagger = _integer(cfg, "stagger_minutes", 0, 30)
    finale = _integer(cfg, "finale_minutes", 15, 90)
    if type(cfg["surprise_enabled"]) is not bool:
        raise ValueError("surprise_enabled must be true or false")
    if (team_slots - 1) * stagger + 30 > duration - finale:
        raise ValueError("The final team needs at least 30 minutes before the finale")
    end = (start.astimezone(timezone.utc) + timedelta(minutes=duration)).astimezone(zone)
    # This is a human host sheet, not an event scheduler: avoid DST offsets
    # changing mid-session and producing confusing printed local clock times.
    if end.utcoffset() != start.utcoffset():
        raise ValueError("Event spans a timezone clock change; choose another window")
    finale_start = (end.astimezone(timezone.utc) - timedelta(minutes=finale)).astimezone(zone)
    starts = [
        (start.astimezone(timezone.utc) + timedelta(minutes=i * stagger)).astimezone(zone)
        for i in range(team_slots)
    ]
    bonus = None
    if cfg["surprise_enabled"]:
        digest = hashlib.sha256((event_id + ":" + cfg["start_local"] + ":" + theme).encode("utf-8")).digest()
        bonus = BONUSES[int.from_bytes(digest[:4], "big") % len(BONUSES)]
    return {
        "schema_version": SCHEMA,
        "status": "planning_only_unverified",
        "event_id": event_id,
        "title": title,
        "theme": theme,
        "theme_description": THEMES[theme],
        "timezone": zone_name,
        "venue_label": venue,
        "starts_local": [s.isoformat(timespec="minutes") for s in starts],
        "start_utc": start.astimezone(timezone.utc).isoformat(timespec="minutes"),
        "finale_local": finale_start.isoformat(timespec="minutes"),
        "end_local": end.isoformat(timespec="minutes"),
        "team_slots": team_slots,
        "photo_cards": [{"stop": i + 1, "prompt": p} for i, p in enumerate(PROMPTS)],
        "optional_bonus": bonus,
        "warning": NOTICE,
        "sharing": PRIVACY,
        "player_integration": "none; existing QR/pack/player workflows remain separate",
    }


def render_html(manifest: dict) -> str:
    e = lambda value: html.escape(str(value), quote=True)
    rows = "\n".join(
        f"<tr><th scope='row'>Slot {i}</th><td>{e(t)}</td></tr>"
        for i, t in enumerate(manifest["starts_local"], 1)
    )
    cards = "\n".join(
        f"<section class='card'><h3>Optional card {entry['stop']}</h3>"
        f"<p>{e(entry['prompt'])}</p><p>Sketch, describe, or capture only with consent.</p></section>"
        for entry in manifest["photo_cards"]
    )
    bonus = (
        f"<section class='card'><h3>Optional, noncompetitive surprise</h3>"
        f"<p>{e(manifest['optional_bonus'])}</p></section>"
        if manifest["optional_bonus"] else ""
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{e(manifest['title'])} — host planning kit (unverified)</title>
<style>
body{{max-width:52rem;margin:2rem auto;padding:0 1rem;font:1rem/1.55 system-ui,sans-serif;color:#17233b}}
header{{border-bottom:3px solid #223d67;padding-bottom:1rem}}
.warning{{border:2px solid #6a4e0f;background:#fff4cf;padding:1rem}}
table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;border:1px solid #888;padding:.5rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}}
.card{{border:1px solid #64748b;border-radius:.5rem;padding:1rem;break-inside:avoid}}
@media print{{body{{max-width:initial;margin:0}}.card{{page-break-inside:avoid}}}}
</style></head><body>
<header><p>ZQM Labs · Host planning example · No app or backend provided by this file</p>
<h1>{e(manifest['title'])}</h1><p>{e(manifest['theme_description'])}</p></header>
<p class="warning"><strong>Not a public event announcement.</strong> {e(manifest['warning'])}</p>
<h2>Host-run schedule, not automatic unlocks</h2>
<p>Timezone: {e(manifest['timezone'])}. Venue: {e(manifest['venue_label'])}.
Check local permits, permissions, safe crossings, emergency procedures and accessible alternatives.</p>
<table><caption>Suggested, noncompetitive staggered starts</caption>
<thead><tr><th scope="col">Anonymous team slot</th><th scope="col">Local start with UTC offset</th></tr></thead>
<tbody>{rows}</tbody></table>
<p>Optional shared finale: {e(manifest['finale_local'])}. End: {e(manifest['end_local'])}.
Do not rush or require everyone to arrive simultaneously. Offer flexible participation.</p>
<h2>Six optional observation / sharing cards</h2>
<p>{e(manifest['sharing'])}</p><div class="cards">{cards}{bonus}</div>
<h2>Organizer release checklist</h2>
<ul><li>Validate an independently approved six-stop quest and the real player/kit versions.</li>
<li>Confirm venue and sign permissions, accessible routes and weather alternatives.</li>
<li>Use the existing private QR-sign kit to generate actual join and stop codes;
this HTML does not create a join link, issue codes, publish an event, or check entitlements.</li>
<li>Do not expose player positions, collect photo metadata or publish images without consent.</li>
<li>Record a field/device playtest and separately validate payment/fulfillment if offered commercially.</li></ul>
</body></html>
"""


def build(config_path: Path, output_dir: Path) -> dict:
    manifest = compile_event(load_config(config_path))
    if output_dir.exists():
        raise ValueError("Refusing to overwrite existing output directory")
    output_dir.mkdir(parents=True)
    (output_dir / "host-sheet.html").write_text(render_html(manifest), encoding="utf-8")
    (output_dir / "event-plan.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Fresh output directory")
    args = parser.parse_args()
    try:
        manifest = build(args.config, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(f"Wrote static host planning kit: {args.output} ({manifest['event_id']})")
    print(NOTICE)


if __name__ == "__main__":
    main()
