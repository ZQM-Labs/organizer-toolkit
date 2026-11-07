# Host-owned Community Day kit generator

**Status:** working *offline planning generator* and four synthetic sample
configurations. Not an activated quest, a ticketing service, live-ops scheduler,
published city route, automatic GPS unlock, or verified player integration.

This tool converts a host-reviewed event outline into a static, printable
HTML host sheet and a machine-readable JSON schedule. It is separate from the
six-stop quest-pack contract and requires **no server, player account, API,
telemetry, photo upload, or new paid dependency**.

## Generate a sample

Python 3.11+ and operating-system IANA timezone data are required.

From the repository root:

```bash
python event-kit/build_event.py \
  event-kit/examples/community-day.sample.json \
  --output out/community-day
```

The output directory must not already exist; this prevents overwriting a
previous plan. Open `out/community-day/host-sheet.html` in a browser and print
it. `event-plan.json` records the same schedule and optional cards.
Both are local files; publishing or distributing either is a separate action.

Additional **example-only** themes:

- `event-kit/examples/heritage-walk.sample.json` — an illustrative heritage program
- `event-kit/examples/team-day.sample.json` — noncompetitive team cooperation
- `event-kit/examples/seasonal-pop-up.sample.json` — a themed seasonal event

Dates, venues and group sizes are fictional planning fixtures, not real
bookings. Create a new private configuration for a genuine venue after the
host has agreed to the route, permissions, accessibility and supervision.

## Exact configuration schema

The source uses a strict v1 planning schema, not the quest-player pack schema.

| Field | What it means |
| --- | --- |
| `schema_version` | Must be the integer `1` |
| `event_id` | A short lowercase identifier; never a player identifier |
| `event_title` | Public-safe working title |
| `theme` | One of `community`, `heritage`, `school`, `team`, or `seasonal` |
| `timezone` | IANA time zone, e.g., `America/New_York` |
| `start_local` | Local wall-clock start, `YYYY-MM-DDTHH:MM` |
| `duration_minutes` | 60–480 inclusive |
| `team_slots` | 1–20 anonymous schedule positions, no participant roster |
| `stagger_minutes` | 0–30; safety/queue management, not a timed race |
| `finale_minutes` | 15–90; an optional gathering window near the end |
| `venue_label` | Public-safe host description; avoid precise private addresses |
| `surprise_enabled` | Boolean; one deterministic **optional, noncompetitive** prompt |

Unknown or duplicate keys, malformed values, overlong text, impossible
team windows, and ambiguous/nonexistent daylight-saving local start times
are rejected. Events that span a clock change are also rejected; adjust
the host plan rather than silently mis-scheduling people. Event times in
the exported sheet include the local UTC offset.

The final team has at least 30 minutes before the proposed finale. This
is a *minimum validation rule*, not a claim that a six-stop route can be
completed in 30 minutes. Hosts must test actual route distances, terrain,
breaks and access needs, and move the finale or extend the window
accordingly. A participant must be able to skip the finale or take a
different pace.

## What the optional cards actually do

Six original observation prompts accompany the six-stop format. They
can be read aloud, sketched or discussed; photographs and short clips are
**optional**. Capturing or distributing any image requires the relevant
consent and rights. Do not photograph strangers, homes, students, license
plates, private interiors, or sensitive locations. Strip EXIF location
metadata and avoid real-time publication of participant positions. The
tool **does not** capture, store, process, geolocate or upload photos.

The optional surprise is selected deterministically from four
noncompetitive, stationary reflection prompts using a hash of the
event identifier, planned start, and theme. All hosts using the same
configuration get the same result. It grants **no digital reward, unlock,
ranking points, extra physical stop, or incentive to rush**.

There are **no** public status boards, lures, crowd signals, live participant
tracking, waiting-room APIs, automated start restrictions, PWA changes, or
background scheduling in this implementation.

## Integration with the current products

1. The organizer separately uses the existing
   [QR sign generator](../qr-kit/README.md) with a **private** reviewed
   kit configuration, approved six-stop location, current player version
   and access policy. Never put paid access codes or private keys into
   this public example repository.
2. The actual story/puzzle content remains in
   [quest-packs](https://github.com/ZQM-Labs/quest-packs); the mandatory
   six-stop structure and validator remain in
   [quest-authoring](https://github.com/ZQM-Labs/quest-authoring).
3. The host, not the tool, manages local time announcements, attendance,
   weather contingency and accessible alternatives. The schedule is
   human-readable reference data, **not** an automatic player lock.
4. Verify the exact game, event and device configuration using
   [ZQM Labs playtests](https://github.com/ZQM-Labs/playtests).
5. Before a commercial launch, independently verify pricing, support
   capacity, booking, checkout, fulfillment and any required permits.

You may display a physical **"game in progress"** notice only with venue
approval and without exposing player routes or live positions. An
optional host-issued paper completion stamp is safer than an account-based
global badge system at this stage.

## Test and release gates

```bash
python -m unittest discover -s tests -p 'test_event_kit.py' -v
python scripts/check_docs.py
```

The tests cover deterministic local/UTC times, time-zone transitions,
strict schemas, privacy-sensitive extra keys, HTML escaping, the original
six-card count, sample configs, and overwrite refusal.

A green CI result proves the **planning files**, not that a real event
has been hosted or a route is safe. Do not advertise a "Community Day"
booking, timed raid, photo collection, or seasonal edition until the
corresponding venue, player, pack and operational release gates pass.
